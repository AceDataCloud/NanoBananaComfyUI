"""Fixed-host Nano Banana API client for ComfyUI.

Paid submissions are sent once. Only task lookups and media downloads retry.
"""

from __future__ import annotations

import ipaddress
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import requests

BASE_URL = "https://api.acedata.cloud"
IMAGE_HOSTS = {"cdn.acedata.cloud", "cdn.acedata2.cloud"}
MAX_IMAGE_BYTES = 32 * 1024 * 1024
COMPLETE = {"complete", "completed", "succeed", "succeeded", "success", "finished"}
FAILED = {"failed", "error", "cancelled", "canceled", "rejected"}
MODELS = (
    "nano-banana",
    "nano-banana-2-lite",
    "nano-banana-2",
    "nano-banana-2.1",
    "nano-banana-pro",
    "nano-banana:official",
    "nano-banana-2-lite:official",
    "nano-banana-2:official",
    "nano-banana-pro:official",
)
ASPECT_RATIOS = ("1:1", "3:2", "2:3", "16:9", "9:16", "4:3", "3:4")
RESOLUTIONS = ("1K", "2K", "4K")


class NanoBananaError(RuntimeError):
    """A customer-safe error without raw responses, URLs, or credentials."""


def _credential() -> str:
    token = os.environ.get("ACEDATACLOUD_API_KEY") or os.environ.get("ACEDATACLOUD_API_TOKEN")
    if not token or not token.strip():
        raise NanoBananaError(
            "Set ACEDATACLOUD_API_KEY in the ComfyUI process environment and restart ComfyUI."
        )
    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise NanoBananaError("Ace Data Cloud API key is empty.")
    return token


def _post(path: str, payload: dict[str, Any], *, read_only: bool = False) -> dict[str, Any] | list[Any]:
    token = _credential()
    for attempt in range(3 if read_only else 1):
        try:
            response = requests.post(
                BASE_URL + path,
                json=payload,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=(10, 60 if read_only else 45),
                allow_redirects=False,
            )
            break
        except requests.RequestException as exc:
            if read_only and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            operation = "query" if read_only else "submission"
            raise NanoBananaError(
                f"Nano Banana {operation} connection failed ({type(exc).__name__}). "
                "Inspect the task or request history before submitting another paid operation."
            ) from None
    if not 200 <= response.status_code < 300:
        raise NanoBananaError(
            f"Ace Data Cloud returned HTTP {response.status_code}. "
            "Check service access, balance, and request history before retrying."
        )
    try:
        body = response.json()
    except ValueError:
        raise NanoBananaError("Ace Data Cloud returned invalid JSON.") from None
    if not isinstance(body, (dict, list)):
        raise NanoBananaError("Ace Data Cloud returned an unexpected response.")
    if isinstance(body, dict) and (body.get("success") is False or body.get("error")):
        raise NanoBananaError("Nano Banana reported an error. Inspect the task or trace ID.")
    return body


def _validate_public_https(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.hostname
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("Reference images must use public HTTPS URLs.")
    if host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith(".local"):
        raise ValueError("Reference images must use public HTTPS URLs.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Reference images must use public HTTPS URLs.")
    return url.strip()


def parse_reference_urls(value: str) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("At least one reference image URL is required for editing.")
    raw = value.strip()
    if raw.startswith("["):
        try:
            urls = json.loads(raw)
        except ValueError:
            raise ValueError("Reference image URLs must be a JSON array or one URL per line.") from None
    else:
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(urls, list) or not urls or not all(isinstance(x, str) for x in urls):
        raise ValueError("At least one reference image URL is required for editing.")
    return list(dict.fromkeys(_validate_public_https(url) for url in urls))


def _result(body: dict[str, Any] | list[Any], *, retrieved: bool) -> Any:
    result: Any = body.get("response", body) if retrieved and isinstance(body, dict) else body
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            result = {}
    return result if result is not None else {}


def _image_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"request", "request_body", "input", "prompt"}:
                    continue
                if key in {"image_url", "raw_image_url", "url"} and isinstance(child, str):
                    if child.startswith("https://"):
                        urls.append(child)
                elif key == "image_urls" and isinstance(child, list):
                    urls.extend(url for url in child if isinstance(url, str) and url.startswith("https://"))
                elif isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return list(dict.fromkeys(urls))


def _states(value: Any) -> tuple[list[str], bool]:
    states: list[str] = []
    has_error = False

    def walk(item: Any) -> None:
        nonlocal has_error
        if isinstance(item, dict):
            if item.get("success") is False or item.get("error"):
                has_error = True
            for key, child in item.items():
                if key in {"state", "status"} and isinstance(child, str):
                    states.append(child.lower())
                elif key in {"data", "content", "task"}:
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return states, has_error


def _normalize(body: dict[str, Any] | list[Any], task_id: str = "", *, retrieved: bool = False) -> tuple[str, str, list[str], str]:
    result = _result(body, retrieved=retrieved)
    outer = body if isinstance(body, dict) else {}
    inner = result if isinstance(result, dict) else {}
    task_id = str(task_id or outer.get("task_id") or inner.get("task_id") or
                  (outer.get("task", {}).get("id") if isinstance(outer.get("task"), dict) else "") or "")
    trace_id = str(inner.get("trace_id") or outer.get("trace_id") or "")
    unfinished = retrieved and "finished_at" in outer and outer["finished_at"] is None
    states, has_error = _states(result)
    urls = _image_urls(result)
    if (has_error or any(state in FAILED for state in states)) and not unfinished:
        raise NanoBananaError("Nano Banana task failed. Inspect its task or trace ID.")
    done = not unfinished and ((bool(states) and all(state in COMPLETE for state in states)) or
                               (bool(urls) and not states) or
                               (retrieved and bool(outer.get("finished_at")) and bool(result) and not states))
    if done:
        if not urls:
            raise NanoBananaError("Nano Banana task finished without an image URL.")
        return "succeeded", task_id, urls, trace_id
    if task_id:
        return "pending", task_id, [], trace_id
    raise NanoBananaError("No task ID or completed image was returned. Inspect request history before resubmitting.")


def _submit(action: str, prompt: str, model: str, aspect_ratio: str, resolution: str,
            count: int, image_urls: list[str] | None = None) -> tuple[str, str, list[str], str]:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt is required.")
    if model not in MODELS:
        raise ValueError("Unsupported Nano Banana model.")
    if aspect_ratio not in ASPECT_RATIOS or resolution not in RESOLUTIONS:
        raise ValueError("Unsupported aspect ratio or resolution.")
    if not isinstance(count, int) or not 1 <= count <= 4:
        raise ValueError("Count must be from 1 to 4.")
    payload: dict[str, Any] = {
        "action": action, "prompt": prompt.strip(), "model": model,
        "aspect_ratio": aspect_ratio, "resolution": resolution, "count": count, "async": True,
    }
    if image_urls is not None:
        payload["image_urls"] = image_urls
    body = _post("/nano-banana/images", payload)
    return _normalize(body)


def generate(prompt: str, model: str, aspect_ratio: str, resolution: str,
             count: int) -> tuple[str, str, list[str], str]:
    return _submit("generate", prompt, model, aspect_ratio, resolution, count)


def edit(prompt: str, model: str, aspect_ratio: str, resolution: str,
         count: int, reference_urls: str) -> tuple[str, str, list[str], str]:
    return _submit("edit", prompt, model, aspect_ratio, resolution, count,
                   parse_reference_urls(reference_urls))


def retrieve_once(task_id: str) -> tuple[str, str, list[str], str]:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("A Nano Banana task ID is required.")
    body = _post("/nano-banana/tasks", {"action": "retrieve", "id": task_id.strip()}, read_only=True)
    return _normalize(body, task_id.strip(), retrieved=True)


def retrieve(task_id: str, wait_seconds: int) -> tuple[str, str, list[str], str]:
    if not isinstance(wait_seconds, int) or not 0 <= wait_seconds <= 240:
        raise ValueError("Wait seconds must be from 0 to 240.")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = retrieve_once(task_id)
        if result[0] != "pending" or time.monotonic() >= deadline:
            return result
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def retrieve_batch(ids_json: str) -> list[dict[str, Any]]:
    try:
        ids = json.loads(ids_json)
    except (TypeError, ValueError):
        raise ValueError("Task IDs must be a JSON array.") from None
    if not isinstance(ids, list) or not ids or not all(isinstance(x, str) and x.strip() for x in ids):
        raise ValueError("Task IDs must be a nonempty JSON array of strings.")
    body = _post("/nano-banana/tasks", {"action": "retrieve_batch", "ids": ids}, read_only=True)
    items = body if isinstance(body, list) else body.get("items", body.get("tasks", body.get("data", [])))
    if not isinstance(items, list):
        raise NanoBananaError("Nano Banana returned an invalid batch result.")
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("id") or item.get("task_id") or "")
        try:
            status, task_id, urls, trace_id = _normalize(item, task_id, retrieved=True)
        except NanoBananaError:
            status, urls, trace_id = "failed", [], ""
        results.append({"status": status, "task_id": task_id,
                        "image_urls": urls, "trace_id": trace_id})
    return results


def parse_result_urls(value: str) -> list[str]:
    try:
        urls = json.loads(value)
    except (TypeError, ValueError):
        raise ValueError("Image URLs must be a JSON array.") from None
    if not isinstance(urls, list) or not urls or not all(isinstance(x, str) for x in urls):
        raise ValueError("Image URLs must be a nonempty JSON array of strings.")
    return urls


def download_image(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in IMAGE_HOSTS or parsed.username or parsed.password:
        raise NanoBananaError("Image URL must be an Ace Data Cloud HTTPS media link.")
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(10, 60), allow_redirects=False) as response:
                if response.status_code != 200:
                    raise NanoBananaError(f"Image download returned HTTP {response.status_code}.")
                claimed = int(response.headers.get("Content-Length", "0"))
                if claimed > MAX_IMAGE_BYTES:
                    raise NanoBananaError("Image exceeds the 32 MiB limit.")
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_IMAGE_BYTES:
                        raise NanoBananaError("Image exceeds the 32 MiB limit.")
                    chunks.append(chunk)
            if not size:
                raise NanoBananaError("Image download was empty.")
            return b"".join(chunks)
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise NanoBananaError(f"Image download failed ({type(exc).__name__}).") from None
    raise AssertionError("Unreachable")
