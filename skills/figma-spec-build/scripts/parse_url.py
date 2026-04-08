#!/usr/bin/env python3
"""Parse a Figma URL into fileKey + nodeId.

Usage:
    python3 parse_url.py "https://www.figma.com/design/KEY/Name?node-id=1-2&m=dev"

Output (stdout): JSON {"fileKey": "...", "nodeId": "1:2", "fileName": "Name", "url": "..."}

Exit codes:
    0 success
    2 URL is unparseable or unsupported (board URLs, missing node-id)
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import parse_qs, urlparse


class UrlParseError(ValueError):
    """Raised when the URL cannot be turned into a (fileKey, nodeId) pair."""


def parse_figma_url(url: str) -> dict[str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise UrlParseError(f"unsupported URL scheme: {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if host not in {"figma.com", "www.figma.com"}:
        raise UrlParseError(f"not a figma.com URL: {parsed.hostname!r}")

    segments = [seg for seg in parsed.path.split("/") if seg]
    if len(segments) < 2:
        raise UrlParseError(f"path too short: {parsed.path!r}")

    kind = segments[0]
    if kind == "board":
        raise UrlParseError("FigJam/board URLs are not supported by this skill")
    if kind == "make":
        # figma.com/make/:makeFileKey/:makeFileName
        file_key = segments[1]
        file_name = segments[2] if len(segments) >= 3 else ""
    elif kind == "design":
        # figma.com/design/:fileKey/:fileName
        # or figma.com/design/:fileKey/branch/:branchKey/:fileName
        if len(segments) >= 4 and segments[2] == "branch":
            file_key = segments[3]
            file_name = segments[4] if len(segments) >= 5 else ""
        else:
            file_key = segments[1]
            file_name = segments[2] if len(segments) >= 3 else ""
    else:
        raise UrlParseError(f"unsupported figma URL kind: {kind!r}")

    if not file_key:
        raise UrlParseError("fileKey is empty")

    query = parse_qs(parsed.query)
    node_raw = (query.get("node-id") or [""])[0]
    if not node_raw:
        raise UrlParseError("node-id query param is required")
    # Convert hyphen notation to colon notation: "19030-97432" -> "19030:97432"
    node_id = node_raw.replace("-", ":")

    return {
        "fileKey": file_key,
        "nodeId": node_id,
        "fileName": file_name,
        "url": url.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a Figma URL")
    parser.add_argument("url", help="Figma frame URL")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent")
    args = parser.parse_args()

    try:
        payload = parse_figma_url(args.url)
    except UrlParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
