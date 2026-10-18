import unittest
import io
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from scripts.translate_docs import (
    protect_markdown,
    request_spark,
    restore_markdown,
    sync_paths,
    translation_paths,
)


class TranslateDocsTests(unittest.TestCase):
    def test_translates_each_markdown_file_separately(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            source_root = repository_root / "doc"
            output_root = repository_root / "doc-en"
            source_root.mkdir()
            (source_root / "first.md").write_text("First document", encoding="utf-8")
            (source_root / "second.md").write_text("Second document", encoding="utf-8")
            paths = [Path("doc/first.md"), Path("doc/second.md")]

            with patch("scripts.translate_docs.translate_text", side_effect=lambda text, _password, _model: text) as translate:
                sync_paths(paths, source_root, output_root, "test-password", "lite")

        self.assertEqual(translate.call_count, 2)
        self.assertEqual([call.args[0] for call in translate.call_args_list], ["First document", "Second document"])

    def test_retries_temporary_http_500_then_succeeds(self):
        error_body = b'{"error":{"message":"read message from mom expired","code":"10300"}}'
        success_body = json.dumps({"code": 0, "choices": []}).encode("utf-8")
        response = io.BytesIO(success_body)

        with patch(
            "scripts.translate_docs.urllib.request.urlopen",
            side_effect=[HTTPError("https://example.com", 500, "Server Error", {}, io.BytesIO(error_body)), response],
        ) as urlopen, patch("scripts.translate_docs.time.sleep") as sleep:
            result = request_spark(Request("https://example.com"))

        self.assertEqual(result["code"], 0)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)

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