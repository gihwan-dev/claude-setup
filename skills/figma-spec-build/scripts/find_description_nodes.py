#!/usr/bin/env python3
"""Find "Description" frame nodes inside a get_metadata XML dump.

The Figma MCP `get_metadata` tool returns XML where each frame/text node has
attributes id, name, x, y, width, height. This script walks the tree and
returns the Description frames + their parent screen frames.

Primary match: frame with attribute name="Description".
Fallback match (if primary yields zero): frames at x=1920 whose descendant
text elements include one named "Description".

Usage:
    python3 find_description_nodes.py --metadata path/to/metadata.xml|.json

Output (stdout): JSON array of objects:
    [
      {
        "node_id": "19030:110405",
        "parent_node_id": "19030:97432",
        "parent_name": "MORANSQ010",
        "x": 1920.0, "y": 0.0, "width": 401.0, "height": 1080.0,
        "match": "name" | "fallback"
      },
      ...
    ]
Sorted by (parent_y, parent_x, y).

Exit codes:
    0 success (including zero matches, with empty array)
    1 invalid input file
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator


_XML_INVALID_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"  # control chars disallowed in XML 1.0
)


def _load_xml_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    if stripped.startswith("["):
        # MCP wrapper: [{"type": "text", "text": "<xml>"}]
        data = json.loads(raw)
        text = ""
        for entry in data:
            if isinstance(entry, dict) and entry.get("type") == "text":
                text = entry.get("text", "")
                if text:
                    break
        if not text:
            raise ValueError("no text entry found in JSON wrapper")
    else:
        text = raw
    # Figma occasionally embeds control chars (e.g. \x08) in layer names.
    # Strip them so ElementTree doesn't reject the document.
    return _XML_INVALID_CHARS_RE.sub("", text)


def _wrap_root(xml_text: str) -> str:
    """Ensure the XML has a single synthetic root to handle any fragment input."""
    return f"<_root>{xml_text}</_root>"


def _parse_float(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _find_top_screen_frame(
    element: ET.Element, parents: list[ET.Element]
) -> ET.Element | None:
    """Find the outermost screen frame ancestor (NOT the synthetic root).

    If the Description is at arbitrary depth, its "parent screen" is typically
    the outermost frame other than the synthetic root. We walk up until we
    reach the synthetic root.
    """
    if not parents:
        return None
    # parents[0] is the synthetic root; parents[1] is the outermost real frame.
    if len(parents) >= 2:
        return parents[1]
    return parents[0] if parents[0].tag != "_root" else None


def _iter_with_parents(
    root: ET.Element,
) -> Iterator[tuple[ET.Element, list[ET.Element]]]:
    stack: list[tuple[ET.Element, list[ET.Element]]] = [(root, [])]
    while stack:
        node, parents = stack.pop()
        yield node, parents
        child_parents = parents + [node]
        for child in list(node):
            stack.append((child, child_parents))


def _has_description_text_child(node: ET.Element) -> bool:
    for descendant in node.iter("text"):
        if (descendant.get("name") or "").strip() == "Description":
            return True
    return False


def find_description_nodes(xml_text: str) -> list[dict[str, object]]:
    # Strip XML-illegal control characters that Figma occasionally embeds
    xml_text = _XML_INVALID_CHARS_RE.sub("", xml_text)
    wrapped = _wrap_root(xml_text)
    try:
        root = ET.fromstring(wrapped)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc

    primary: list[dict[str, object]] = []
    fallback_candidates: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for node, parents in _iter_with_parents(root):
        if node.tag != "frame":
            continue
        node_id = (node.get("id") or "").strip()
        name = (node.get("name") or "").strip()
        if not node_id or node_id in seen_ids:
            continue

        top = _find_top_screen_frame(node, parents)
        parent_id = (top.get("id") if top is not None else "") or ""
        parent_name = (top.get("name") if top is not None else "") or ""
        # If this node IS the top screen frame, skip (no self-parent).
        if top is None or top is node:
            continue

        entry = {
            "node_id": node_id,
            "parent_node_id": parent_id,
            "parent_name": parent_name,
            "x": _parse_float(node.get("x")),
            "y": _parse_float(node.get("y")),
            "width": _parse_float(node.get("width")),
            "height": _parse_float(node.get("height")),
            "parent_x": _parse_float(top.get("x")),
            "parent_y": _parse_float(top.get("y")),
        }

        if name == "Description":
            entry["match"] = "name"
            primary.append(entry)
            seen_ids.add(node_id)
            continue

        # Fallback candidate: right column (x ~= 1920) with Description text child
        if abs(entry["x"] - 1920.0) < 1.0 and _has_description_text_child(node):
            entry["match"] = "fallback"
            fallback_candidates.append(entry)

    results = primary if primary else fallback_candidates
    # Dedup fallback (name-matched nodes always win)
    deduped: dict[str, dict[str, object]] = {}
    for entry in results:
        deduped[entry["node_id"]] = entry  # type: ignore[assignment]

    ordered = sorted(
        deduped.values(),
        key=lambda e: (e["parent_y"], e["parent_x"], e["y"], e["x"]),  # type: ignore[index]
    )
    # Strip helper parent_x/parent_y before output
    for entry in ordered:
        entry.pop("parent_x", None)
        entry.pop("parent_y", None)
    return ordered  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find Description frame nodes inside Figma get_metadata XML"
    )
    parser.add_argument(
        "--metadata",
        required=True,
        help="Path to metadata file (raw XML or JSON wrapper from MCP)",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indent")
    args = parser.parse_args()

    path = Path(args.metadata)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        xml_text = _load_xml_text(path)
        results = find_description_nodes(xml_text)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(results, ensure_ascii=False, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
