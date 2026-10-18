[中文 README](/README.md) | [English README](/doc-en/README.md)

# 文档翻译工作流

当 `doc/` 目录中的文件发生提交变更时，GitHub Actions 会调用讯飞星火 HTTP API 翻译变更的 Markdown，并把图片等非 Markdown 文件同步到 `doc-en/`，保留原有的相对目录结构。

## 配置 API 密钥

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加 `SPARK_API_PASSWORD`，值为讯飞开放平台星火 HTTP 服务的 APIPassword。该密钥只在 Actions 环境中使用，不要写入仓库文件。

工作流默认使用 `lite` 模型。首次配置密钥后，可在 **Actions → Translate documentation → Run workflow** 手动运行一次，生成全部英文文档。

## Markdown 导航链接

每篇 Markdown 文档开头都应包含指向中文 README 和 English README 的根路径链接。翻译器会保留链接目标、代码和 URL；译文写入 `doc-en/` 下对应路径，图片和其他静态文件也会复制到对应位置。