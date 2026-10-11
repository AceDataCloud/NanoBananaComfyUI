# Ace Data Cloud Nano Banana ComfyUI 节点

通过 Ace Data Cloud 的 Nano Banana 云 API 生成或编辑图片，按**同一个任务 ID**查询终态，再将成品加载为 ComfyUI 标准 `IMAGE`。无需本地模型或显卡；生成与编辑会按[当前价格](https://platform.acedata.cloud/models)扣除 Ace Data Cloud Credits。

[English](../README.md) · [控制台](https://platform.acedata.cloud/console/applications)

节点包括生成、编辑、单任务查询、批量任务查询、单图加载和多图批量加载。生成和编辑只提交一次收费请求；查询及下载不会重新生成。包覆盖 Dify Nano Banana 插件目前列出的 9 个模型 ID：`nano-banana`、`nano-banana-2-lite`、`nano-banana-2`、`nano-banana-2.1`、`nano-banana-pro` 及除 `2.1` 外上述四种模型的 `:official` 版本。不同模型的价格与分辨率能力可能不同；`nano-banana` 和 `nano-banana-2-lite` 只支持 `1K`。

## 安装与密钥

Registry 版本激活后，在 ComfyUI-Manager 搜索 **Nano Banana**，核对 publisher 为 `acedatacloud`、包名为 **Nano Banana by Ace Data Cloud** 后安装并重启。发布前可在 ComfyUI 的 `custom_nodes` 目录克隆本仓库，并运行 `python -m pip install -r requirements.txt` 测试源码。

在**运行 ComfyUI 的进程环境**设置 `ACEDATACLOUD_API_KEY`，然后重启。也接受 `ACEDATACLOUD_API_TOKEN`。密钥不可写入工作流 JSON、仓库、截图或 issue。若启用 API 路径限制，请放行 `/nano-banana/images` 和 `/nano-banana/tasks`。

## 首次运行

1. 用 **File → Open** 导入 [提交工作流](../examples/01-submit-nano-banana.json)，选择模型和价格，只运行一次，复制 Preview as Text 显示的任务 ID。提交成功不代表图片已经生成；超时且无任务 ID 时先查请求历史，不要直接重试收费提交。
2. 导入[查询与预览工作流](../examples/02-retrieve-and-preview.json)，填入同一任务 ID。它连接 **Retrieve Task → Load Images → Preview Image**。若 240 秒后仍为 pending，只重新运行查询工作流。`succeeded` 且图片真正显示，才算完成。
3. 编辑图片时，导入[编辑工作流](../examples/03-edit-nano-banana.json)，把占位地址改成公开 HTTPS 参考图 URL；可以一行一个，也可以填 JSON 数组。编辑仍走 `/nano-banana/images`，`action` 为 `edit`。拿到任务 ID 后复用查询工作流。

在[控制台](https://platform.acedata.cloud/console/applications)按任务或 trace ID 核对 Credits 记录。HTTP 401/403 检查密钥和服务权限；429 等待限流；提交超时或 5xx 先核对历史，避免重复扣费。插件会把提示词和参考图 URL 发送给 Ace Data Cloud，完成后从 Ace CDN 下载图片。只提交有权处理的内容，详见[隐私说明](PRIVACY.md)。
