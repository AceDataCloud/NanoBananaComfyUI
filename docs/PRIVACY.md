# Privacy and network behavior

- The plugin reads `ACEDATACLOUD_API_KEY` or `ACEDATACLOUD_API_TOKEN` from the ComfyUI process environment. It does not put the key in a workflow or save it to disk.
- Generate and Edit send the prompt, selected model, generation settings, and edit reference URLs to the fixed `https://api.acedata.cloud/nano-banana/images` endpoint. These are paid operations and are never retried automatically.
- Retrieve and Retrieve Batch query `https://api.acedata.cloud/nano-banana/tasks` with existing task IDs. Only these read-only calls may retry a transient network failure.
- Load Image and Load Images download completed media from `cdn.acedata.cloud` or `cdn.acedata2.cloud` over HTTPS, with redirects disabled and a 32 MiB per-image limit.
- The plugin contacts only the fixed Ace API and the Ace CDN hosts above; it does not install runtime packages, run shell commands, or collect telemetry.
- A ComfyUI workflow may contain prompts, reference URLs, task IDs, and result URLs. Review it before sharing; keep the Ace API key in the process environment.
