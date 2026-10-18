#!/usr/bin/env python3
"""Translate Markdown documentation with the iFlytek Spark HTTP API."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"
DEFAULT_MODEL = "lite"
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`+|~+)[ \t]*(?:\r?\n)?$")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)
LINK_TARGET_RE = re.compile(r"(?<=\]\()(?P<target><[^>\n]+>|[^)\s]+)")
URL_RE = re.compile(r"https?://[^\s)>]+|mailto:[^\s)>]+")


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


def translate_text(text: str, api_password: str, model: str) -> str:
    masked, protected = protect_markdown(text)
    system_prompt = (
        "Translate the supplied Chinese Markdown documentation into natural English. "
        "Return only the translated Markdown, with no explanation or outer code fence. "
        "Preserve every Markdown heading, list, table, admonition, line break, identifier, "
        "and document structure. Do not translate or modify placeholder tokens; they mark "
        "code, link targets, URLs, and other content that must remain exact."
    )
    request_body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": masked},
            ],
            "temperature": 0.2,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=request_body,
        headers={
            "Authorization": f"Bearer {api_password}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Spark API returned HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach Spark API: {error.reason}") from error

    if result.get("code", 0) != 0:
        raise RuntimeError(f"Spark API error: {result.get('message', result)}")
    try:
        translated = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"Unexpected Spark API response: {result}") from error

    restored = restore_markdown(translated.strip(), protected)
    return restored.rstrip() + "\n"


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
    paths: list[Path], source_root: Path, output_root: Path, api_password: str, model: str
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
            translated = translate_text(source_text, api_password, model)
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
    password = os.environ.get("SPARK_API_PASSWORD", "")
    model = os.environ.get("SPARK_MODEL", DEFAULT_MODEL)

    if not password:
        print("SPARK_API_PASSWORD is required (set it as a GitHub Actions secret).", file=sys.stderr)
        return 2

    if bool(args.base_ref) != bool(args.head_ref):
        parser.error("--base-ref and --head-ref must be supplied together")
    try:
        if args.base_ref and not args.base_ref.startswith("0" * 40):
            paths = changed_paths(args.base_ref, args.head_ref)
        else:
            paths = [path.relative_to(repository_root) for path in source_root.rglob("*") if path.is_file()]
        sync_paths(paths, source_root, output_root, password, model)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())