"""ComfyUI graph nodes for Nano Banana tasks and image output."""

from __future__ import annotations

import json
from io import BytesIO

from .client import (
    ASPECT_RATIOS,
    MODELS,
    RESOLUTIONS,
    NanoBananaError,
    download_image,
    edit,
    generate,
    parse_result_urls,
    retrieve,
    retrieve_batch,
)


def _submission(result):
    status, task_id, urls, trace_id = result
    if not task_id and not urls:
        raise NanoBananaError("No task ID or image was returned.")
    return {"ui": {"text": [f"Nano Banana status: {status}",
                            f"Task ID: {task_id or 'completed synchronously'}",
                            "Use Retrieve with this task ID; do not resubmit to poll." if task_id and not urls
                            else "Image is ready."]},
            "result": (status, task_id, json.dumps(urls), trace_id)}


class AceNanoBananaGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "A watercolor landscape at sunrise."}),
            "model": (list(MODELS), {"default": "nano-banana-2-lite"}),
            "aspect_ratio": (list(ASPECT_RATIOS), {"default": "1:1"}),
            "resolution": (list(RESOLUTIONS), {"default": "1K"}),
            "count": ("INT", {"default": 1, "min": 1, "max": 4}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "task_id", "image_urls_json", "trace_id")
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Submit one paid Nano Banana generation. Retrieve the same task ID to collect images."
    OUTPUT_NODE = True

    def run(self, prompt: str, model: str, aspect_ratio: str, resolution: str, count: int):
        return _submission(generate(prompt, model, aspect_ratio, resolution, count))


class AceNanoBananaEdit:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "Change the background to a starry night."}),
            "reference_image_urls": ("STRING", {"multiline": True, "default": ""}),
            "model": (list(MODELS), {"default": "nano-banana-2-lite"}),
            "aspect_ratio": (list(ASPECT_RATIOS), {"default": "1:1"}),
            "resolution": (list(RESOLUTIONS), {"default": "1K"}),
            "count": ("INT", {"default": 1, "min": 1, "max": 4}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "task_id", "image_urls_json", "trace_id")
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Edit public HTTPS reference images. Enter a JSON URL array or one URL per line."
    OUTPUT_NODE = True

    def run(self, prompt: str, reference_image_urls: str, model: str,
            aspect_ratio: str, resolution: str, count: int):
        return _submission(edit(prompt, model, aspect_ratio, resolution, count,
                                reference_image_urls))


class AceNanoBananaRetrieve:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "task_id": ("STRING", {"default": ""}),
            "wait_seconds": ("INT", {"default": 240, "min": 0, "max": 240, "step": 5}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "task_id", "image_urls_json", "first_image_url", "trace_id")
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Read the same task. Connect image URLs to Load Images after success."
    OUTPUT_NODE = True

    def run(self, task_id: str, wait_seconds: int):
        status, task_id, urls, trace_id = retrieve(task_id, wait_seconds)
        return {"ui": {"text": [f"Nano Banana status: {status}", f"Task ID: {task_id}",
                                f"Images ready: {len(urls)}" if urls else "Query this task ID again later"]},
                "result": (status, task_id, json.dumps(urls), urls[0] if urls else "", trace_id)}


class AceNanoBananaRetrieveBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"task_ids_json": ("STRING", {"multiline": True, "default": "[]"})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("results_json",)
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Read multiple existing task IDs without submitting new generations."
    OUTPUT_NODE = True

    def run(self, task_ids_json: str):
        results = retrieve_batch(task_ids_json)
        return {"ui": {"text": [f"Retrieved {len(results)} Nano Banana tasks"]},
                "result": (json.dumps(results),)}


def _image_tensor(raw: bytes):
    import numpy as np
    import torch
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(raw)) as image:
            image.load()
            rgb = image.convert("RGB")
            array = np.asarray(rgb, dtype=np.float32).copy() / 255.0
    except (UnidentifiedImageError, OSError, ValueError):
        raise NanoBananaError("The media link does not contain a valid image.") from None
    return torch.from_numpy(array).unsqueeze(0)


class AceNanoBananaLoadImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image_url": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Load one completed Ace Data Cloud image as a ComfyUI IMAGE tensor."

    def run(self, image_url: str):
        if not image_url:
            raise NanoBananaError("Task is still pending. Query the same task ID again.")
        return (_image_tensor(download_image(image_url)),)


class AceNanoBananaLoadImages:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image_urls_json": ("STRING", {"multiline": True, "default": "[]"})}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Nano Banana"
    DESCRIPTION = "Load a completed result's image URL array as a ComfyUI IMAGE batch."

    def run(self, image_urls_json: str):
        import torch

        urls = parse_result_urls(image_urls_json)
        images = [_image_tensor(download_image(url)) for url in urls]
        dimensions = {(image.shape[1], image.shape[2]) for image in images}
        if len(dimensions) != 1:
            raise NanoBananaError("Images have different sizes; load them one at a time.")
        return (torch.cat(images, dim=0),)
