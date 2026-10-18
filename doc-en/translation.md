[中文 README](/README.md) | [English README](/doc-en/README.md)

# Documentation Translation Workflow

When commits change files in the `doc/` directory, GitHub Actions calls the free online Index-Translate API to translate the changed Markdown files. It also synchronizes non-Markdown files, such as images, to `doc-en/`, preserving the original relative directory structure. Each Markdown file is requested individually, with at least a 0.5-second interval between calls (up to 2 calls per second), and retries are performed for temporary service errors.

## Online API

The workflow uses the officially public OpenAI-compatible interface `https://index-translate.bilibili.com/v1/chat/completions` provided by Index-Translate, with `Index-Translate-35B-A3B` as the default model. This interface requires no API key or GPU, and no GitHub Actions Secrets need to be configured. The model disables thinking and has an output budget of 8192 tokens.

For the first run or when regenerating all translations, you can manually start the workflow by going to **Actions → Translate documentation → Run workflow**.

## Markdown Navigation Links

Each Markdown document should begin with root-path links to the Chinese README and the English README. The translator preserves link targets, code, and URLs. The translated text is written to the corresponding path under `doc-en/`, and images and other static files are also copied to their respective locations.
