import unittest
from pathlib import Path

from scripts.translate_docs import protect_markdown, restore_markdown


class TranslateDocsTests(unittest.TestCase):
    def test_protects_code_links_and_urls(self):
        source = (
            "[中文 README](/README.md) | [English README](/doc-en/README.md)\n\n"
            "标题 [访问](../guide.md)\n\n"
            "`inline code` and https://example.com/path\n\n"
            "```python\nprint('hello')\n```\n"
        )
        masked, protected = protect_markdown(source)

        self.assertNotIn("../guide.md", masked)
        self.assertNotIn("/README.md", masked)
        self.assertNotIn("print('hello')", masked)
        self.assertEqual(restore_markdown(masked, protected), source)

    def test_rejects_missing_or_changed_placeholder(self):
        _, protected = protect_markdown("`keep me`")
        token = next(iter(protected))
        with self.assertRaises(ValueError):
            restore_markdown(f"{token} {token}", protected)


if __name__ == "__main__":
    unittest.main()