#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DIRECTIVE_PATTERN = re.compile(
    r"\b(must|always|never|forbid|forbidden|guardrail|fallback|checklist|rule|rules)\b|"
    "\\uBC18\\uB4DC\\uC2DC|\\uD56D\\uC0C1|\\uAE08\\uC9C0|\\uD558\\uC9C0 \\uB9D0\\uC544\\uC57C \\uD560 \\uAC83|\\uCCB4\\uD06C\\uB9AC\\uC2A4\\uD2B8|\\uADDC\\uCE59|\\uAC00\\uB4DC\\uB808\\uC77C",
    re.IGNORECASE,
)
FALLBACK_PATTERN = re.compile(r"\bfallback\b", re.IGNORECASE)
FRONTMATTER_BOUNDARY = "---"


@dataclass(frozen=True)
class SkillAudit:
    skill: str
    path: str
    score: float
    reasons: list[str]
    metrics: dict[str, Any]


def _collect_skill_dirs(skills_root: Path) -> list[Path]:
    return sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and not path.name.startswith("_") and (path / "SKILL.md").exists()
    )


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0].strip() != FRONTMATTER_BOUNDARY:
        return {}, markdown

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_BOUNDARY:
            end_index = index
            break
    if end_index is None:
        return {}, markdown

    meta_lines = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    metadata: dict[str, str] = {}
    index = 0
    while index < len(meta_lines):
        raw_line = meta_lines[index]
        if not raw_line.strip():
            index += 1
            continue
        if ":" not in raw_line:
            index += 1
            continue
        key, raw_value = raw_line.split(":", 1)
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
                metadata[key] = " ".join("\n".join(block_lines).split())
            else:
                metadata[key] = "\n".join(block_lines).strip()
            continue
        metadata[key] = raw_value.strip('"').strip("'")
        index += 1
    return metadata, body


def _normalize_bullet(line: str) -> str:
    normalized = line.strip()
    normalized = re.sub(r"^[-*]\s+", "", normalized)
    normalized = normalized.replace("`", "")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def _score_skill(skill_dir: Path, skills_root: Path) -> SkillAudit:
    skill_path = skill_dir / "SKILL.md"
    markdown = skill_path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(markdown)

    lines = markdown.splitlines()
    body_lines = body.splitlines()
    nonempty_body_lines = [line for line in body_lines if line.strip()]
    body_line_count = len(nonempty_body_lines)

    description = metadata.get("description", "")
    description_length = len(description)
    fallback_hits = len(FALLBACK_PATTERN.findall(markdown))
    bullet_lines = [line for line in body_lines if line.lstrip().startswith("- ")]
    normalized_bullets = [_normalize_bullet(line) for line in bullet_lines if _normalize_bullet(line)]

    duplicate_rule_lines = 0
    seen: dict[str, int] = {}
    for bullet in normalized_bullets:
        seen[bullet] = seen.get(bullet, 0) + 1
    duplicate_rule_lines = sum(count - 1 for count in seen.values() if count > 1)

    directive_bullets = [line for line in bullet_lines if DIRECTIVE_PATTERN.search(line)]
    rule_density = (len(directive_bullets) / body_line_count) if body_line_count else 0.0

    has_references = (skill_dir / "references").is_dir()
    has_agents_openai = (skill_dir / "agents" / "openai.yaml").exists()

    score = 0.0
    reasons: list[str] = []

    line_penalty = max(0, len(lines) - 120) / 6
    score += line_penalty
    if len(lines) > 120:
        reasons.append(f"SKILL.md has {len(lines)} lines, so body compression should be a high priority.")
    if len(lines) > 180:
        score += 6.0
        reasons.append("The body is long enough that workflow and reference splitting is likely needed.")

    description_penalty = max(0, description_length - 260) / 45
    score += description_penalty
    if description_length > 260:
        reasons.append(
            f"The frontmatter description is {description_length} characters long and has room to be compressed around triggers."
        )

    fallback_penalty = fallback_hits * 3.0
    score += fallback_penalty
    if fallback_hits:
        reasons.append(
            f"The term `fallback` appears {fallback_hits} times, so accumulated compatibility explanations should be reviewed."
        )

    duplicate_penalty = duplicate_rule_lines * 4.0
    score += duplicate_penalty
    if duplicate_rule_lines:
        reasons.append(
            f"There are {duplicate_rule_lines} duplicate bullet rules, which suggests checklist duplication."
        )

    if rule_density > 0.22:
        density_penalty = (rule_density - 0.22) * 70
        score += density_penalty
        reasons.append(
            f"Directive bullet density is high ({rule_density:.0%}), which may mean the body has grown into a rule list."
        )

    if not has_references and body_line_count > 80:
        score += 8.0 + ((body_line_count - 80) / 8)
        reasons.append("The body is long without a `references/` directory, so it is a strong split candidate.")

    if not has_agents_openai:
        score += 2.0
        reasons.append("`agents/openai.yaml` is missing, so explicit invocation metadata should be evaluated.")

    if not metadata.get("name"):
        score += 20.0
        reasons.append("Frontmatter `name` is missing or could not be parsed.")
    if not description:
        score += 20.0
        reasons.append("Frontmatter `description` is missing or could not be parsed.")

    if not reasons:
        reasons.append("No major compression signal was found, but the skill still belongs in periodic audits.")

    metrics = {
        "line_count": len(lines),
        "body_line_count": body_line_count,
        "description_length": description_length,
        "fallback_hits": fallback_hits,
        "duplicate_rule_lines": duplicate_rule_lines,
        "rule_density": round(rule_density, 4),
        "has_references": has_references,
        "has_agents_openai": has_agents_openai,
    }
    return SkillAudit(
        skill=skill_dir.name,
        path=str(skill_path.relative_to(skills_root)),
        score=round(score, 2),
        reasons=reasons,
        metrics=metrics,
    )


def _resolve_scope(skills_root: Path, skill_names: list[str], raw_paths: list[str]) -> list[Path]:
    if not skill_names and not raw_paths:
        return _collect_skill_dirs(skills_root)

    selected: dict[str, Path] = {}
    for name in skill_names:
        path = skills_root / name
        if not (path / "SKILL.md").exists():
            raise FileNotFoundError(f"skill not found: {name}")
        selected[path.name] = path

    for raw_path in raw_paths:
        path = Path(raw_path).expanduser().resolve()
        if path.is_file() and path.name == "SKILL.md":
            path = path.parent
        if not (path / "SKILL.md").exists():
            raise FileNotFoundError(f"skill path not found: {raw_path}")
        selected[path.name] = path

    return sorted(selected.values())


def _render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Audited {payload['scope_count']} skill(s) under {payload['skills_root']}",
        f"Showing top {payload['reported_count']} result(s)",
    ]
    for index, result in enumerate(payload["results"], start=1):
        metrics = result["metrics"]
        lines.append(
            f"{index}. {result['skill']} score={result['score']:.2f} "
            f"lines={metrics['line_count']} desc={metrics['description_length']} "
            f"fallback={metrics['fallback_hits']} refs={'yes' if metrics['has_references'] else 'no'} "
            f"agent={'yes' if metrics['has_agents_openai'] else 'no'}"
        )
        for reason in result["reasons"]:
            lines.append(f"   - {reason}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local skills and rank refactor candidates")
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parents[3] / "skills"),
        help="Path to the canonical skills directory",
    )
    parser.add_argument("--skill", action="append", default=[], help="Skill name to audit")
    parser.add_argument("--path", action="append", default=[], help="Skill directory or SKILL.md path")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to print")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than 0")

    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.is_dir():
        print(f"skills root not found: {skills_root}", file=sys.stderr)
        return 2

    try:
        scope = _resolve_scope(skills_root, args.skill, args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    results = [_score_skill(skill_dir, skills_root) for skill_dir in scope]
    results.sort(key=lambda item: (-item.score, item.skill))
    limited_results = results[: args.limit]

    payload = {
        "skills_root": str(skills_root),
        "scope_count": len(results),
        "reported_count": len(limited_results),
        "results": [asdict(result) for result in limited_results],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
