#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import tomllib
import sys
from pathlib import Path

HEADER = """<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Run: python3 scripts/sync_instructions.py -->"""

GLOBAL_HEADER = """<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Installed to ~/.codex/AGENTS.md as global Codex policy. -->"""

_REPO_ONLY_RE = re.compile(r"<!--\s*repo-only\s*-->")


def load_manifest(policy_root: Path) -> dict[str, object]:
    manifest_path = policy_root / "_manifest.toml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"policy manifest not found: {manifest_path}")
    return tomllib.loads(manifest_path.read_text(encoding="utf-8"))


def load_sections(policy_root: Path, section_names: list[str]) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for name in section_names:
        path = policy_root / name
        if not path.exists():
            raise FileNotFoundError(f"policy section not found: {path}")
        sections.append((name, path.read_text(encoding="utf-8").strip()))
    return sections


def build_instructions_content(title: str, sections: list[tuple[str, str]]) -> str:
    body = "\n\n".join(section for _, section in sections).strip()
    return f"{HEADER}\n\n# {title}\n\n{body}\n"


def build_agents_content(sections: list[tuple[str, str]]) -> str:
    detail_links = "\n".join(f"- [{name}](docs/policy/{name})" for name, _ in sections)
    body = f"""# Repository Guidance

세부 정책은 `docs/policy/*.md`와 `CONTRIBUTING.md`를 본다.

## Core Goal

- 메인 스레드는 전략과 의사결정에 집중한다.
- 실행 작업은 필요한 경우에만 위임하고, 간결한 요약만 반환받는다.

## Source Of Truth

- 정책 authoring source: `docs/policy/*.md`
- agent contract: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- skill canonical source: `skills/`
- generated output: `INSTRUCTIONS.md`, `AGENTS.md`, `CLAUDE.md`, `skills/INDEX.md`, `skills/manifest.json`, `agents/*.md`, `dist/codex/*`

## Required Commands

```bash
python3 scripts/sync_instructions.py
python3 scripts/sync_agents.py
python3 scripts/sync_skills_index.py
python3 scripts/validate_workflow_contracts.py
python3 scripts/install_assets.py --dry-run --target all
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Important Constraints

- delegated lane에서 writer 위임은 조건부다. 메인 스레드가 기본 구현자이며, 대규모 변경 시 파일 경계가 명확한 작업만 writer에 위임한다.
- planning role은 internal-only다.
- `skills/`가 canonical source다.
- `.agents/skills`는 install-time legacy overlay일 뿐 canonical source가 아니다.
- generated file은 직접 수정하지 않고 source를 고친 뒤 sync로 재생성한다.

## Detailed Policy Files

{detail_links}
"""
    return f"{HEADER}\n\n{body.strip()}\n"


def _filter_repo_only_lines(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not _REPO_ONLY_RE.search(line)
    )


def build_global_agents_content(sections: list[tuple[str, str]]) -> str:
    body = "\n\n".join(
        _filter_repo_only_lines(section) for _, section in sections
    ).strip()
    preamble = (
        "# Multi-Agent Orchestration Policy\n\n"
        "이 정책은 모든 프로젝트에 적용되는 Codex global orchestration 규칙이다.\n"
        "프로젝트별 추가 규칙은 해당 프로젝트의 `AGENTS.md`를 참조한다."
    )
    return f"{GLOBAL_HEADER}\n\n{preamble}\n\n{body}\n"


def build_claude_content() -> str:
    body = """# Claude Code Project Memory

루트 메모리는 얇게 유지한다. 세부 정책은 아래 source 파일을 import한다.

@AGENTS.md
@CONTRIBUTING.md
"""
    return f"{HEADER}\n\n{body.strip()}\n"


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
        description="Sync docs/policy into INSTRUCTIONS.md, AGENTS.md, and CLAUDE.md"
    )
    parser.add_argument("--check", action="store_true", help="Check drift only")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    policy_root = repo_root / "docs" / "policy"
    instructions_path = repo_root / "INSTRUCTIONS.md"
    agents_path = repo_root / "AGENTS.md"
    claude_path = repo_root / "CLAUDE.md"
    global_agents_path = repo_root / "dist" / "codex" / "AGENTS.md"

    if not policy_root.exists():
        print(f"policy source not found: {policy_root}", file=sys.stderr)
        return 1

    manifest = load_manifest(policy_root)
    title = str(manifest["title"])
    section_names = list(manifest["sections"])
    sections = load_sections(policy_root, section_names)

    global_section_names = list(manifest.get("global_sections", section_names))
    global_sections = load_sections(policy_root, global_section_names)

    instructions_content = build_instructions_content(title, sections)
    agents_content = build_agents_content(sections)
    claude_content = build_claude_content()
    global_agents_content = build_global_agents_content(global_sections)

    instructions_ok = check_or_write(instructions_path, instructions_content, args.check)
    agents_ok = check_or_write(agents_path, agents_content, args.check)
    claude_ok = check_or_write(claude_path, claude_content, args.check)
    global_agents_ok = check_or_write(global_agents_path, global_agents_content, args.check)

    if args.check:
        if instructions_ok and agents_ok and claude_ok and global_agents_ok:
            print("sync-instructions: up to date")
            return 0
        if not instructions_ok:
            print(f"drift: {instructions_path}")
        if not agents_ok:
            print(f"drift: {agents_path}")
        if not claude_ok:
            print(f"drift: {claude_path}")
        if not global_agents_ok:
            print(f"drift: {global_agents_path}")
        return 1

    print("ok  INSTRUCTIONS.md")
    print("ok  AGENTS.md")
    print("ok  CLAUDE.md")
    print("ok  dist/codex/AGENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
