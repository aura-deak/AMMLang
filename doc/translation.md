[中文 README](/README.md) | [English README](/doc-en/README.md)

# 文档翻译工作流

当 `doc/` 目录中的文件发生提交变更时，GitHub Actions 会调用 Index-Translate 免费在线 API 翻译变更的 Markdown，并把图片等非 Markdown 文件同步到 `doc-en/`，保留原有的相对目录结构。每篇 Markdown 单独请求，调用间至少间隔 0.5 秒（最多每秒 2 次），并对临时服务错误进行重试。

## 在线 API

工作流使用 Index-Translate 官方公开的 OpenAI 兼容接口 `https://index-translate.bilibili.com/v1/chat/completions`，默认模型为 `Index-Translate-35B-A3B`。该接口无需 API 密钥或 GPU，不需要配置 GitHub Actions Secret。模型关闭 thinking，输出预算为 8192 tokens。

首次运行或重新生成全部译文时，可在 **Actions → Translate documentation → Run workflow** 手动启动工作流。

## Markdown 导航链接

每篇 Markdown 文档开头都应包含指向中文 README 和 English README 的根路径链接。翻译器会保留链接目标、代码和 URL；译文写入 `doc-en/` 下对应路径，图片和其他静态文件也会复制到对应位置。