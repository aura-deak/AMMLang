#!/usr/bin/env python3
"""Translate Markdown documentation with the Index-Translate public API."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://index-translate.bilibili.com/v1/chat/completions"
DEFAULT_MODEL = "Index-Translate-35B-A3B"
MAX_OUTPUT_TOKENS = 8192
MAX_API_ATTEMPTS = 4
MAX_CONTENT_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2
MIN_REQUEST_INTERVAL_SECONDS = 0.5
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`+|~+)[ \t]*(?:\r?\n)?$")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)
LINK_TARGET_RE = re.compile(r"(?<=\]\()(?P<target><[^>\n]+>|[^)\s]+)")
URL_RE = re.compile(r"https?://[^\s)>]+|mailto:[^\s)>]+")


class RequestRateLimiter:
    def __init__(self, interval: float = MIN_REQUEST_INTERVAL_SECONDS) -> None:
        self.interval = interval
        self.next_request_at = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delay = self.next_request_at - now
        if delay > 0:
            time.sleep(delay)
        self.next_request_at = max(now, self.next_request_at) + self.interval


API_RATE_LIMITER = RequestRateLimiter()


def protect_markdown(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}

    def replace(value: str) -> str:
        token = f"`MMLANG_KEEP_{len(protected):04d}`"
        protected[token] = value
        return token

    lines = text.splitlines(keepends=True)
    masked_lines: list[str] = []
    index = 0
    while index < len(lines):
        opening = FENCE_OPEN_RE.match(lines[index])
        if opening is None:
            masked_lines.append(INLINE_CODE_RE.sub(lambda match: replace(match.group(0)), lines[index]))
            index += 1
            continue

        fence = opening.group(1)
        block = [lines[index]]
        index += 1
        while index < len(lines):
            block.append(lines[index])
            closing = FENCE_CLOSE_RE.match(lines[index])
            index += 1
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence):
                break
        masked_lines.append(replace("".join(block)))

    masked = "".join(masked_lines)
    masked = LINK_TARGET_RE.sub(lambda match: replace(match.group("target")), masked)
    masked = URL_RE.sub(lambda match: replace(match.group(0)), masked)
    return masked, protected


def restore_markdown(text: str, protected: dict[str, str]) -> str:
    for token, original in protected.items():
        if text.count(token) != 1:
            raise ValueError(f"Translation did not preserve protected token {token}")
        text = text.replace(token, original)
    return text


def strip_think(text: str) -> str:
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip().removeprefix("<think>").strip()


def request_translation_api(request: urllib.request.Request) -> dict:
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            API_RATE_LIMITER.wait()
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            if error.code not in (429, 500, 502, 503, 504) or attempt == MAX_API_ATTEMPTS:
                raise RuntimeError(f"Index-Translate API returned HTTP {error.code}: {details}") from error
            failure = f"HTTP {error.code}: {details}"
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == MAX_API_ATTEMPTS:
                reason = getattr(error, "reason", error)
                raise RuntimeError(f"Could not reach Index-Translate API after {attempt} attempts: {reason}") from error
            failure = f"network error: {getattr(error, 'reason', error)}"
        else:
            error_code = str(result.get("code", "0"))
            if error_code == "0":
                return result
            if error_code not in {"10300", "10007"} or attempt == MAX_API_ATTEMPTS:
                raise RuntimeError(f"Index-Translate API error: {result.get('message', result)}")
            failure = f"API error {error_code}: {result.get('message', result)}"

        delay = RETRY_BASE_SECONDS * (2 ** (attempt - 1))
        print(
            f"Index-Translate API temporary failure ({failure}); retrying in {delay}s "
            f"({attempt}/{MAX_API_ATTEMPTS - 1}).",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(delay)

    raise RuntimeError("Index-Translate API request exhausted its retry attempts")


def translate_text(text: str, model: str) -> str:
    masked, protected = protect_markdown(text)
    base_system_prompt = (
        "Translate the supplied Chinese Markdown documentation into natural English. "
        "Return only the translated Markdown, with no explanation or outer code fence. "
        "Preserve every Markdown heading, list, table, admonition, line break, identifier, "
        "and document structure. Every MMLANG_KEEP token in backticks must appear exactly "
        "once in your response, unchanged and in its original position. These tokens stand "
        "for code, link targets, URLs, and other content that must remain exact."
    )
    for content_attempt in range(1, MAX_CONTENT_ATTEMPTS + 1):
        system_prompt = base_system_prompt
        if content_attempt > 1:
            system_prompt += (
                " The previous response failed validation. Ensure all listed protected "
                "tokens appear exactly once: " + ", ".join(protected)
            )
        request_body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": masked},
                ],
                "temperature": 0.0,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            API_URL,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Index-Translate-Client/1.0",
            },
            method="POST",
        )

        result = request_translation_api(request)
        try:
            translated = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError(f"Unexpected Index-Translate API response: {result}") from error

        try:
            restored = restore_markdown(strip_think(translated), protected)
        except ValueError as error:
            if content_attempt == MAX_CONTENT_ATTEMPTS:
                raise
            print(
                f"{error}; retrying this document ({content_attempt}/{MAX_CONTENT_ATTEMPTS - 1}).",
                file=sys.stderr,
                flush=True,
            )
            continue
        return restored.rstrip() + "\n"

    raise RuntimeError("Index-Translate translation failed content validation")


def changed_paths(base_ref: str, head_ref: str) -> list[Path]:
    output = subprocess.run(
        [
            "git", "diff", "--name-only", "--no-renames", "-z",
            base_ref, head_ref, "--", "doc",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return [Path(name.decode("utf-8")) for name in output.split(b"\0") if name]


def translation_paths(
    source_root: Path, repository_root: Path, base_ref: str | None, head_ref: str | None
) -> list[Path]:
    if base_ref and head_ref and not base_ref.startswith("0" * 40):
        paths = changed_paths(base_ref, head_ref)
        if paths:
            return paths
        print("No changed files under doc/; translating all documentation.")

    return [path.relative_to(repository_root) for path in source_root.rglob("*") if path.is_file()]


def remove_empty_parents(path: Path, root: Path) -> None:
    parent = path.parent
    while parent != root:
        try:
            parent.relative_to(root)
        except ValueError:
            break
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def sync_paths(
    paths: list[Path], source_root: Path, output_root: Path, model: str
) -> None:
    for relative_path in paths:
        if relative_path.is_absolute() or ".." in relative_path.parts or relative_path.parts[0] != "doc":
            raise ValueError(f"Refusing path outside doc/: {relative_path}")

        source_path = source_root / relative_path.relative_to("doc")
        output_path = output_root / relative_path.relative_to("doc")
        if not source_path.is_file():
            output_path.unlink(missing_ok=True)
            remove_empty_parents(output_path, output_root)
            print(f"Removed {output_path}")
        elif source_path.suffix.lower() == ".md":
            source_text = source_path.read_text(encoding="utf-8")
            print(f"Translating {source_path}", flush=True)
            translated = translate_text(source_text, model)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(translated, encoding="utf-8")
            print(f"Translated {source_path} -> {output_path}")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, output_path)
            print(f"Copied {source_path} -> {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="Translate only paths changed between these refs")
    parser.add_argument("--head-ref", help="Head ref for --base-ref")
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parent.parent
    source_root = repository_root / "doc"
    output_root = repository_root / "doc-en"
    model = os.environ.get("INDEX_TRANSLATE_MODEL", DEFAULT_MODEL)

    if bool(args.base_ref) != bool(args.head_ref):
        parser.error("--base-ref and --head-ref must be supplied together")
    try:
        paths = translation_paths(source_root, repository_root, args.base_ref, args.head_ref)
        sync_paths(paths, source_root, output_root, model)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())