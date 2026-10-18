import unittest
import io
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from scripts.translate_docs import (
    API_URL,
    DEFAULT_MODEL,
    MAX_OUTPUT_TOKENS,
    protect_markdown,
    RequestRateLimiter,
    request_translation_api,
    restore_markdown,
    strip_think,
    sync_paths,
    translate_text,
    translation_paths,
)


class TranslateDocsTests(unittest.TestCase):
    def test_strips_optional_thinking_block(self):
        self.assertEqual(strip_think("<think>reasoning</think>Translated text"), "Translated text")
        self.assertEqual(strip_think("<think>partial"), "partial")

    def test_rate_limiter_enforces_two_requests_per_second(self):
        limiter = RequestRateLimiter(interval=0.5)
        with patch("scripts.translate_docs.time.monotonic", side_effect=[10.0, 10.1, 10.5]), patch(
            "scripts.translate_docs.time.sleep"
        ) as sleep:
            limiter.wait()
            limiter.wait()
            limiter.wait()

        delays = [call.args[0] for call in sleep.call_args_list]
        self.assertEqual(len(delays), 2)
        self.assertAlmostEqual(delays[0], 0.4)
        self.assertAlmostEqual(delays[1], 0.5)

    def test_retries_document_when_model_drops_protected_token(self):
        masked, protected = protect_markdown("说明 `important code`。")
        token = next(iter(protected))
        valid_translation = masked.replace("说明", "Description")
        responses = [
            {"choices": [{"message": {"content": "Description."}}]},
            {"choices": [{"message": {"content": valid_translation}}]},
        ]

        with patch("scripts.translate_docs.request_translation_api", side_effect=responses) as request:
            translated = translate_text("说明 `important code`。", DEFAULT_MODEL)

        self.assertEqual(translated, "Description `important code`。\n")
        self.assertEqual(request.call_count, 2)
        api_request = request.call_args_list[0].args[0]
        self.assertEqual(api_request.full_url, API_URL)
        self.assertEqual(api_request.get_header("User-agent"), "Index-Translate-Client/1.0")
        self.assertIsNone(api_request.get_header("Authorization"))
        payload = json.loads(api_request.data)
        self.assertEqual(payload["model"], DEFAULT_MODEL)
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["max_tokens"], MAX_OUTPUT_TOKENS)
        self.assertEqual(payload["chat_template_kwargs"], {"enable_thinking": False})
        retry_payload = json.loads(request.call_args_list[1].args[0].data)
        self.assertIn(token, retry_payload["messages"][0]["content"])

    def test_translates_each_markdown_file_separately(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            source_root = repository_root / "doc"
            output_root = repository_root / "doc-en"
            source_root.mkdir()
            (source_root / "first.md").write_text("First document", encoding="utf-8")
            (source_root / "second.md").write_text("Second document", encoding="utf-8")
            paths = [Path("doc/first.md"), Path("doc/second.md")]

            with patch("scripts.translate_docs.translate_text", side_effect=lambda text, _model: text) as translate:
                sync_paths(paths, source_root, output_root, DEFAULT_MODEL)

        self.assertEqual(translate.call_count, 2)
        self.assertEqual([call.args[0] for call in translate.call_args_list], ["First document", "Second document"])

    def test_retries_temporary_http_500_then_succeeds(self):
        error_body = b'{"error":{"message":"read message from mom expired","code":"10300"}}'
        success_body = json.dumps({"code": 0, "choices": []}).encode("utf-8")
        response = io.BytesIO(success_body)

        with patch(
            "scripts.translate_docs.urllib.request.urlopen",
            side_effect=[HTTPError("https://example.com", 500, "Server Error", {}, io.BytesIO(error_body)), response],
        ) as urlopen, patch("scripts.translate_docs.time.sleep") as sleep, patch(
            "scripts.translate_docs.API_RATE_LIMITER.wait"
        ) as rate_limit:
            result = request_translation_api(Request("https://example.com"))

        self.assertEqual(result["code"], 0)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)
        self.assertEqual(rate_limit.call_count, 2)

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