# Nano Banana for ComfyUI by Ace Data Cloud

Generate or edit images with Nano Banana, retrieve the **same task ID**, and load the completed image into ComfyUI's standard `IMAGE` type. These nodes call a hosted Ace Data Cloud API; no local model or GPU is needed. Generation and editing consume Ace Data Cloud Credits at the [current service price](https://platform.acedata.cloud/models?utm_source=comfyui&utm_medium=referral&utm_campaign=evergreen&utm_content=nanobananacomfyui_readme_en_pricing).

[简体中文](docs/README.zh-CN.md) · [Ace Data Cloud](https://platform.acedata.cloud?utm_source=comfyui&utm_medium=referral&utm_campaign=evergreen&utm_content=nanobananacomfyui_readme_en_home) · [Issues](https://github.com/AceDataCloud/NanoBananaComfyUI/issues)

| Node | Purpose |
| --- | --- |
| **Nano Banana Generate Image** | Submit one paid text-to-image task |
| **Nano Banana Edit Image** | Submit one paid edit using public HTTPS reference image URLs |
| **Nano Banana Retrieve Task** | Query or wait for the same task ID |
| **Nano Banana Retrieve Tasks** | Read multiple existing task IDs without new generation |
| **Nano Banana Load Image / Load Images** | Decode one result URL or a URL array into ComfyUI `IMAGE` |

The package offers all nine model IDs currently listed by the [Ace Data Cloud Dify Nano Banana plugin](https://github.com/AceDataCloud/NanoBananaDify):

`nano-banana`, `nano-banana-2-lite`, `nano-banana-2`, `nano-banana-2.1`, `nano-banana-pro`, `nano-banana:official`, `nano-banana-2-lite:official`, `nano-banana-2:official`, and `nano-banana-pro:official`.

Model availability, resolution limits, and pricing can differ. Check the current service documentation before a paid run. `nano-banana` and `nano-banana-2-lite` support only `1K`; choose a model that supports `2K` or `4K` when requesting those sizes. A count of 1–4 is available; the Load Images node returns a batch when the output images have matching dimensions.


## Current version and install source

This source version is **0.1.2**. Check [GitHub Releases](https://github.com/AceDataCloud/NanoBananaComfyUI/releases) for its versioned ZIP. The Registry section below retains the last verified **Active 0.1.0 on 2026-10-19**; that older ZIP does not contain this release's updated guide, examples or fixes. To use this version, install its GitHub Release ZIP, or select the exact **0.1.2** Registry release once it becomes Active. Do not substitute the initial nightly selection for a verified stable release.

To install the GitHub ZIP, stop ComfyUI and back up any existing node directory. Extract the ZIP contents into `ComfyUI/custom_nodes/nano-banana/` without adding an extra nested directory, run `python -m pip install -r requirements.txt` there, then restart and refresh. Keep the API Token in the actual launch-process environment. A GitHub ZIP install is separate from a verified Registry/Manager stable installation.

## Install

Open the official [Nano Banana by Ace Data Cloud Registry page](https://registry.comfy.org/nodes/nano-banana), or open **Manager → Custom Nodes Manager** and search **Nano Banana**. Use **Ace Data Cloud** as a fallback to find this publisher’s packages. Select **Nano Banana by Ace Data Cloud**, confirm publisher **acedatacloud** and source repository [`AceDataCloud/NanoBananaComfyUI`](https://github.com/AceDataCloud/NanoBananaComfyUI), then click **Install**. In **Select Version**, explicitly select the approved Registry stable release **0.1.0**. The normal dialog may initially highlight **nightly**; do not accept it for this stable-release tutorial. Keep dependency installation enabled. After **Restart Required**, restart ComfyUI and refresh the browser. Registry ID: `nano-banana`.

![Actual ComfyUI-Manager list with this Ace service package](docs/images/manager-discovery.png)

![Actual Manager list after installation and restart](docs/images/manager-installed.png)

These are real **2026-10-16, ComfyUI 0.41.0 Linux** screenshots from the publisher-brand installation test, not a new paid request or a screenshot of service-only search. See [image sources and limits](docs/screenshot-sources.json).

This Registry stable installation was verified on **2026-10-16 with original ComfyUI 0.41.0 on Linux CPU**. That test did not submit a generation or chat request. Newer host versions and each paid action require their own checks; model availability and price remain subject to the current service rules.

For optional local source testing:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/AceDataCloud/NanoBananaComfyUI.git
cd NanoBananaComfyUI
python -m pip install -r requirements.txt
```

Restart ComfyUI and search the node picker for **Nano Banana**. The package uses ComfyUI's existing PyTorch, NumPy, and Pillow installation for image decoding.

## Set your Ace Data Cloud key

### Copy or create your own API Token

The Applications screen is shared across Ace integrations. **1** copies the existing token; **2** opens **Manage Keys**, then **Create**. A new account signs in/registers and initializes **General application** first. Verify this service's access, current price, balance and any expiry/Allowed APIs restrictions.

![Ace Applications: copy token or open Manage Keys](docs/images/get-api-key-en.png)

![Ace Create Key dialog](docs/images/create-api-key-en.png)

These masked **2026-10-08** Ace Console screenshots are reused from SunoDify. The example credential name in the second image is `Dify tutorial`; name yours `ComfyUI`. No credential was created by this guide update. Paste only the token into **the environment of the process that launches ComfyUI** (`ACEDATACLOUD_API_KEY`), then restart. There is no ComfyUI API Key textbox in these nodes; do not paste it into prompt/JSON widgets or the workflow file. An unrelated terminal export does not configure an already-running Desktop process.

1. Sign in to [Ace Data Cloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=comfyui&utm_medium=referral&utm_campaign=evergreen&utm_content=nanobananacomfyui_readme_en_api_key). If your account has no General application, choose **Initialize General Application**.
2. Open **General application** and check access to the service used by this package. A service-specific application key is limited to that service. Copy an existing API key, or choose **Manage Keys → Create** for a separate key named `ComfyUI`.
3. Copy only the token string, without `Bearer ` or quotation marks. A platform management token is not the API key these nodes use. If you enable **Allowed APIs**, include every submission and task-query path used by your workflow. Check current pricing and available Credits before a paid action.

Use an application key with Nano Banana access. Set it in the **ComfyUI process environment** and restart:

```bash
export ACEDATACLOUD_API_KEY='paste-your-key-here'
python main.py --cpu
```

`ACEDATACLOUD_API_TOKEN` is also accepted. Keep the key out of workflows, screenshots, issues, and the repository. If you restrict API paths, allow `/nano-banana/images` and `/nano-banana/tasks`.

## Generate and retrieve

Import [01-submit-nano-banana.json](examples/01-submit-nano-banana.json) with **File → Open**, choose a model and price, then run it once. Copy the task ID from Preview as Text. A submitted task is not a completed image. If submission times out without a task ID, check Ace request history before paying for another generation.

Import [02-retrieve-and-preview.json](examples/02-retrieve-and-preview.json), replace the placeholder task ID, and run it. It connects **Retrieve Task → Load Images → Preview Image**. Retrieve waits up to 240 seconds for the same ID. If still pending, rerun **only** the retrieve workflow. A finished task supplies image URLs; Load Images decodes them into a normal ComfyUI image batch.

For editing, import [03-edit-nano-banana.json](examples/03-edit-nano-banana.json) and replace its placeholder source URL with a public HTTPS reference image. You can also enter a JSON array or one URL per line. It uses the same `/nano-banana/images` endpoint with `action: edit`. Reuse the retrieval workflow for the returned task ID. Reference images are submitted to Ace Data Cloud for processing.

## Check usage and troubleshoot

Check the submitted task or trace ID in the [Ace Data Cloud Console](https://platform.acedata.cloud/console/applications?utm_source=comfyui&utm_medium=referral&utm_campaign=evergreen&utm_content=nanobananacomfyui_readme_en_api_key). Read-only task queries and media downloads should not create another generation.

| Symptom | Action |
| --- | --- |
| Key missing | Put `ACEDATACLOUD_API_KEY` in the actual ComfyUI process environment, then restart. |
| HTTP 401/403 | Check key validity, service access, path restrictions, and content policy. |
| HTTP 429 | Wait for the service limit; keep any accepted task ID. |
| Pending | Query the same task ID again, without rerunning Generate or Edit. |
| Submission timeout or HTTP 5xx | Inspect request history before resubmitting; the paid task may have been accepted. |
| Image download error | Confirm the task succeeded and its Ace media URL is available. |

The nodes send prompts and reference URLs to `api.acedata.cloud`; completed images are downloaded from Ace CDN. See [privacy notes](docs/PRIVACY.md). Only submit content you have permission to process.

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile __init__.py client.py nodes.py
```

`pyproject.toml` declares the short Registry ID `nano-banana`, publisher `acedatacloud`, and a 400×400 proportional resize of the [canonical Ace logo](https://cdn.acedata.cloud/assets/logo.png).

Task lookup nodes refresh the same task on every queued execution rather than reusing a cached pending result. Paid submissions retain stable caching when inputs are unchanged, so refreshing a query does not resubmit generation. Disable auto-queue/auto-run before importing or running these workflows, and explicitly submit once.
