[中文 README](/README.md) | [English README](/doc-en/README.md)

# Documentation Translation Workflow

When files in the `doc/` directory are committed, GitHub Actions will call the free online API of Index-Translate to translate the changed Markdown files. It will also synchronize non-Markdown files, such as images, to `doc-en/`, preserving the original relative directory structure. Each Markdown file is requested individually, with a minimum interval of 0.5 seconds between calls (up to 2 calls per second), and retries are performed for temporary service errors.

## Online API

The workflow uses the officially public OpenAI-compatible interface of Index-Translate at `https://index-translate.bilibili.com/v1/chat/completions`, with the default model set to `Index-Translate-35B-A3B`. This interface requires no API key or GPU, and no configuration of GitHub Actions Secrets is needed. The model has thinking disabled, and the output budget is 8192 tokens.

For the first run or when regenerating all translations, you can manually start the workflow via **Actions → Translate documentation → Run workflow**.

## Markdown Navigation Links

The beginning of each Markdown document should include root-path links to the Chinese README and the English README. The translator will preserve link targets, code, and URLs. The translated text is written to the corresponding path under `doc-en/`, and images and other static files are also copied to their respective locations.
