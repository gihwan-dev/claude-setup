#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

NOTICE_MD = """<!-- AUTO-GENERATED from skills/*/SKILL.md. Do not edit directly. -->
<!-- Run: python3 scripts/sync_skills_index.py -->"""


@dataclass(frozen=True)
class SkillEntry:
    name: str
    description: str
    relative_path: str


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").split())


def _parse_frontmatter(markdown: str, *, path: Path) -> dict[str, str]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"frontmatter not found: {path}")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise ValueError(f"frontmatter closing marker not found: {path}")

    meta_lines = lines[1:end_index]
    meta: dict[str, str] = {}
    index = 0
    while index < len(meta_lines):
        line = meta_lines[index]
        if not line.strip():
            index += 1
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line in {path}: {line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value in {">", "|", ">-", "|-"}:
            block_lines: list[str] = []
            index += 1
            while index < len(meta_lines):
                block_line = meta_lines[index]
                if block_line.startswith("  "):
                    block_lines.append(block_line[2:])
                    index += 1
                    continue
                if not block_line.strip():
                    block_lines.append("")
                    index += 1
                    continue
                break
            if raw_value.startswith(">"):
                value = _normalize_whitespace("\n".join(block_lines))
            else:
                value = "\n".join(block_lines).strip()
            meta[key] = value
            continue

        meta[key] = raw_value.strip('"').strip("'")
        index += 1

    return meta


def _collect_skill_entries(skills_root: Path) -> list[SkillEntry]:
    entries: list[SkillEntry] = []
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if skill_dir.name.startswith("_"):
            continue
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue

        metadata = _parse_frontmatter(
            skill_path.read_text(encoding="utf-8"),
            path=skill_path,
        )
        name = metadata.get("name", "").strip()
        description = _normalize_whitespace(metadata.get("description", ""))
        if not name:
            raise ValueError(f"missing 'name' frontmatter: {skill_path}")
        if name != skill_dir.name:
            raise ValueError(
                f"skill name mismatch: frontmatter={name!r} directory={skill_dir.name!r} ({skill_path})"
            )
        if not description:
            raise ValueError(f"missing 'description' frontmatter: {skill_path}")

        entries.append(
            SkillEntry(
                name=name,
                description=description,
                relative_path=str(skill_path.relative_to(skills_root.parent)),
            )
        )
    return entries


def _render_index(entries: list[SkillEntry]) -> str:
    lines = [
        NOTICE_MD,
        "",
        "# Skills Index",
        "",
        "The canonical skill source is `skills/`. `.agents/skills` is a legacy overlay for install compatibility and is not included in this index.",
        "",
        "## Available Skills",
        "",
    ]
    for entry in entries:
        lines.append(
            f"- `{entry.name}`: {entry.description} (file: `{entry.relative_path}`)"
        )
    lines.append("")
    return "\n".join(lines)


def _render_manifest(entries: list[SkillEntry]) -> str:
    payload = {
        "generated_by": "python3 scripts/sync_skills_index.py",
        "canonical_source_root": "skills",
        "legacy_overlay_root": ".agents/skills",
        "skills": [
            {
                "name": entry.name,
                "description": entry.description,
                "path": entry.relative_path,
            }
            for entry in entries
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _write_or_check(path: Path, expected: str, *, check: bool, drift: list[str]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == expected:
        return
    if check:
        drift.append(str(path))
        return
    path.write_text(expected, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate skills/INDEX.md and skills/manifest.json from skills/*/SKILL.md"
    )
    parser.add_argument("--check", action="store_true", help="Check drift only")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    skills_root = repo_root / "skills"
    entries = _collect_skill_entries(skills_root)

    drift: list[str] = []
    _write_or_check(
        skills_root / "INDEX.md",
        _render_index(entries),
        check=args.check,
        drift=drift,
    )
    _write_or_check(
        skills_root / "manifest.json",
        _render_manifest(entries),
        check=args.check,
        drift=drift,
    )

    if args.check:
        if drift:
            print("sync-skills-index: drift detected")
            for path in drift:
                print(f"drift: {path}")
            return 1
        print("sync-skills-index: up to date")
        return 0

    print(f"ok  {skills_root / 'INDEX.md'}")
    print(f"ok  {skills_root / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
