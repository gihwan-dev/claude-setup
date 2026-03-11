#!/usr/bin/env python3
from __future__ import annotations

import argparse
import tomllib
import sys
from pathlib import Path

HEADER = """<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Run: python3 scripts/sync_instructions.py -->"""


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

Codex용 요약 가이드다. 세부 정책은 `docs/policy/*.md`와 `CONTRIBUTING.md`를 본다.

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

- delegated lane에서는 `worker`만 code diff를 적용한다.
- planning role은 internal-only다.
- `skills/`가 canonical source다.
- `.agents/skills`는 install-time legacy overlay일 뿐 canonical source가 아니다.
- generated file은 직접 수정하지 않고 source를 고친 뒤 sync로 재생성한다.

## Detailed Policy Files

{detail_links}
"""
    return f"{HEADER}\n\n{body.strip()}\n"


def build_claude_content(sections: list[tuple[str, str]]) -> str:
    imports = "\n".join(f"@docs/policy/{name}" for name, _ in sections)
    body = f"""# Claude Code Project Memory

루트 메모리는 얇게 유지한다. 세부 정책은 아래 source 파일을 import한다.

{imports}

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

    if not policy_root.exists():
        print(f"policy source not found: {policy_root}", file=sys.stderr)
        return 1

    manifest = load_manifest(policy_root)
    title = str(manifest["title"])
    section_names = list(manifest["sections"])
    sections = load_sections(policy_root, section_names)

    instructions_content = build_instructions_content(title, sections)
    agents_content = build_agents_content(sections)
    claude_content = build_claude_content(sections)

    instructions_ok = check_or_write(instructions_path, instructions_content, args.check)
    agents_ok = check_or_write(agents_path, agents_content, args.check)
    claude_ok = check_or_write(claude_path, claude_content, args.check)

    if args.check:
        if instructions_ok and agents_ok and claude_ok:
            print("sync-instructions: up to date")
            return 0
        if not instructions_ok:
            print(f"drift: {instructions_path}")
        if not agents_ok:
            print(f"drift: {agents_path}")
        if not claude_ok:
            print(f"drift: {claude_path}")
        return 1

    print("ok  INSTRUCTIONS.md")
    print("ok  AGENTS.md")
    print("ok  CLAUDE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
