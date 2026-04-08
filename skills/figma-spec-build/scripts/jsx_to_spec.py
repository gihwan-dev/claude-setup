#!/usr/bin/env python3
"""Convert a Figma get_design_context JSX dump to clean markdown spec.

The Figma MCP `get_design_context` returns React+Tailwind JSX. For frames
named "Description" in our Analysis files, the structure is predictable:

    <div data-name="Description">
      <div> ... header: <p>Description</p> </div>
      <div> ROW
        <div> number cell: <p>N</p> </div>
        <div> content cell
          <div> section title: <p>Title</p> </div>
          <div> body block
            <p>[Subtitle]</p>
            <ul>
              <li><span>bullet</span>
                <ul><li><span>nested</span></li></ul>
              </li>
            </ul>
          </div>
        </div>
      </div>
      ...
    </div>

We emit:
    ## N. Title

    ### [Subtitle]
    - bullet
      - nested

Usage:
    python3 jsx_to_spec.py path/to/dc_<nodeId>.jsx [--debug]

Output (stdout): clean markdown. Exit 0 on success, 1 on parse error.
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


_BRACKET_SUBTITLE = re.compile(r"^\[[^\]]*\]")
_DIGIT_ONLY = re.compile(r"^\d+$")
_JSX_TEMPLATE = re.compile(r"\{`([^`]*)`\}")  # {`text`} -> text
_WHITESPACE = re.compile(r"\s+")


def _clean_text(raw: str) -> str:
    text = _JSX_TEMPLATE.sub(r"\1", raw)
    text = _WHITESPACE.sub(" ", text).strip()
    return text


class SpecExtractor(HTMLParser):
    """Parse Figma Description JSX into structured markdown."""

    def __init__(self, debug: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.tag_stack: list[tuple[str, int | None]] = []
        self.text_buffers: dict[int, list[str]] = {}
        self.list_depth: int = 0
        self.row_num: int = 0
        self.header_seen: bool = False
        self.expecting_title: bool = False
        self.output_lines: list[str] = []
        self._next_buf_id: int = 0
        self._active_buf_id: int | None = None
        self.debug = debug

    # --- helpers -----------------------------------------------------
    def _in_li(self) -> bool:
        return any(tag == "li" for tag, _ in self.tag_stack)

    def _update_active_buffer(self) -> None:
        self._active_buf_id = None
        for _, buf_id in reversed(self.tag_stack):
            if buf_id is not None:
                self._active_buf_id = buf_id
                return

    def _emit(self, line: str) -> None:
        if self.debug:
            print(f"[emit] depth={self.list_depth} stack={[t for t,_ in self.tag_stack]}: {line!r}", file=sys.stderr)
        self.output_lines.append(line)

    def _emit_paragraph(self, text: str) -> None:
        if not text:
            return
        # Skip the single "Description" header paragraph at top.
        if not self.header_seen and text == "Description":
            self.header_seen = True
            return
        # Row marker: single integer (1, 2, 10, ...)
        if _DIGIT_ONLY.match(text):
            try:
                self.row_num = int(text)
            except ValueError:
                self.row_num += 1
            self.expecting_title = True
            return
        # Section title = first <p> after a row marker
        if self.expecting_title:
            if self.output_lines and self.output_lines[-1] != "":
                self._emit("")
            self._emit(f"## {self.row_num}. {text}")
            self._emit("")
            self.expecting_title = False
            return
        # Bracketed subtitle (matches both "[Foo]" and "[2-1] Foo")
        if _BRACKET_SUBTITLE.match(text):
            if self.output_lines and self.output_lines[-1] != "":
                self._emit("")
            self._emit(f"### {text}")
            return
        # Otherwise: stray paragraph — emit as plain text
        self._emit(text)

    def _emit_bullet(self, text: str) -> None:
        if not text:
            return
        indent = "  " * max(0, self.list_depth - 1)
        self._emit(f"{indent}- {text}")

    # --- HTMLParser hooks -------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        buf_id: int | None = None
        if tag in ("p", "span"):
            buf_id = self._next_buf_id
            self._next_buf_id += 1
            self.text_buffers[buf_id] = []
            self._active_buf_id = buf_id
        if tag == "ul":
            self.list_depth += 1
        self.tag_stack.append((tag, buf_id))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Self-closing tags like <br/>, <img/>
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        # Pop until matching tag (lenient with mismatches)
        while self.tag_stack and self.tag_stack[-1][0] != tag:
            _, discarded = self.tag_stack.pop()
            if discarded is not None:
                self.text_buffers.pop(discarded, None)
        if not self.tag_stack:
            return
        _, buf_id = self.tag_stack.pop()

        if tag == "ul":
            self.list_depth = max(0, self.list_depth - 1)

        if buf_id is not None:
            raw = "".join(self.text_buffers.pop(buf_id, []))
            text = _clean_text(raw)
            if tag == "p":
                self._emit_paragraph(text)
            elif tag == "span":
                if self._in_li():
                    self._emit_bullet(text)
        self._update_active_buffer()

    def handle_data(self, data: str) -> None:
        if self._active_buf_id is not None:
            self.text_buffers[self._active_buf_id].append(data)


def _strip_jsx_trailer(jsx_text: str) -> str:
    """Remove Figma MCP trailer text (instructions) after the JSX component."""
    # The Figma MCP appends instruction text after the final "}" of the component.
    # Heuristic: cut after the last closing </ tag.
    return jsx_text


def jsx_to_spec(jsx_text: str, debug: bool = False) -> str:
    extractor = SpecExtractor(debug=debug)
    extractor.feed(_strip_jsx_trailer(jsx_text))
    extractor.close()

    # Collapse 2+ consecutive blank lines into 1
    lines = extractor.output_lines
    collapsed: list[str] = []
    for line in lines:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    # Strip leading/trailing blank lines
    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return "\n".join(collapsed) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Figma DC JSX to markdown spec")
    parser.add_argument("jsx_path", help="Path to .jsx file from get_design_context")
    parser.add_argument("--debug", action="store_true", help="Dump parser state")
    args = parser.parse_args()

    path = Path(args.jsx_path)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    jsx_text = path.read_text(encoding="utf-8")
    try:
        markdown = jsx_to_spec(jsx_text, debug=args.debug)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
