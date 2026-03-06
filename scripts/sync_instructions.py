#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HEADER = """<!-- AUTO-GENERATED from INSTRUCTIONS.md. Do not edit directly. -->
<!-- Run: ./scripts/sync-instructions.sh -->"""


def build_agents_content(instructions: str) -> str:
    return f"{HEADER}\n\n{instructions}"


def build_claude_content() -> str:
    return f"{HEADER}\n"


def check_or_write(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == content:
        return True
    if check:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync INSTRUCTIONS.md into AGENTS.md and CLAUDE.md"
    )
    parser.add_argument("--check", action="store_true", help="Check drift only")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    instructions_path = repo_root / "INSTRUCTIONS.md"
    agents_path = repo_root / "AGENTS.md"
    claude_path = repo_root / "CLAUDE.md"

    if not instructions_path.exists():
        print(f"INSTRUCTIONS.md not found: {instructions_path}", file=sys.stderr)
        return 1

    instructions = instructions_path.read_text(encoding="utf-8")
    agents_content = build_agents_content(instructions)
    claude_content = build_claude_content()

    agents_ok = check_or_write(agents_path, agents_content, args.check)
    claude_ok = check_or_write(claude_path, claude_content, args.check)

    if args.check:
        if agents_ok and claude_ok:
            print("sync-instructions: up to date")
            return 0
        if not agents_ok:
            print(f"drift: {agents_path}")
        if not claude_ok:
            print(f"drift: {claude_path}")
        return 1

    print("ok  AGENTS.md")
    print("ok  CLAUDE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
