import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from scripts.translate_docs import protect_markdown, restore_markdown, translation_paths


class TranslateDocsTests(unittest.TestCase):
    def test_empty_incremental_diff_falls_back_to_all_docs(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            source_root = repository_root / "doc"
            (source_root / "nested").mkdir(parents=True)
            (source_root / "guide.md").write_text("Guide", encoding="utf-8")
            (source_root / "nested" / "diagram.png").write_bytes(b"image")

            with patch("scripts.translate_docs.changed_paths", return_value=[]):
                paths = translation_paths(source_root, repository_root, "a" * 40, "b" * 40)

        self.assertEqual(set(paths), {Path("doc/guide.md"), Path("doc/nested/diagram.png")})

    def test_nonempty_incremental_diff_stays_incremental(self):
        expected = [Path("doc/guide.md")]
        with patch("scripts.translate_docs.changed_paths", return_value=expected):
            paths = translation_paths(Path("unused"), Path("unused"), "a" * 40, "b" * 40)

        self.assertEqual(paths, expected)

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