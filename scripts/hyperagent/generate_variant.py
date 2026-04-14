#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:  # pragma: no cover - depends on local environment
    anthropic = None  # type: ignore[assignment]


SCHEMA_VERSION = "1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "scripts" / "hyperagent" / "variants"
DEFAULT_PROPOSALS_DIR = REPO_ROOT / "scripts" / "hyperagent" / "proposals"
CLAUDE_MODEL = "claude-sonnet-4-6"


@dataclass(frozen=True)
class Improvement:
    entity_type: str
    entity_id: str
    score: float | None
    priority: str | None
    reason: str
    suggestion: str
    target: str | None
    trend: dict[str, Any] | None
    baseline_delta: float | None
    evidence_sessions: list[str]
    rank: int | None


@dataclass(frozen=True)
class VariantPlan:
    improvement: Improvement
    source_path: Path
    output_path: Path
    meta_path: Path
    variant_id: str
    variant_dir: Path
    relative_variant_dir: str
    modified_filename: str


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("v-%Y%m%d-%H%M%S")


def claude_home() -> Path:
    configured = os.environ.get("CLAUDE_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path("~/.claude").expanduser()


def expand_input_path(raw_path: str) -> Path:
    if raw_path.startswith("~/.claude"):
        suffix = raw_path.removeprefix("~/.claude").lstrip("/")
        return claude_home() / suffix
    return Path(raw_path).expanduser()


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def sanitize_segment(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return sanitized or "unknown"


def load_score_report(path: str | None) -> tuple[dict[str, Any], str]:
    if path:
        source = expand_input_path(path)
        try:
            return json.loads(source.read_text(encoding="utf-8")), str(source)
        except FileNotFoundError:
            raise SystemExit(f"score report not found: {source}") from None
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid score report JSON: {exc}") from None

    if sys.stdin.isatty():
        raise SystemExit("no score report supplied; use --input PATH or pipe JSON on stdin")
    try:
        return json.load(sys.stdin), "stdin"
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid score report JSON from stdin: {exc}") from None


def validate_score_report(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise SystemExit("invalid score report JSON: top-level value must be an object")
    if str(report.get("schema_version")) != SCHEMA_VERSION:
        raise SystemExit('invalid score report JSON: schema_version must be "1"')


def normalize_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def normalize_evidence_sessions(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def normalize_trend(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def improvement_from_row(row: dict[str, Any]) -> Improvement | None:
    entity_type = row.get("entity_type")
    entity_id = row.get("entity_id")
    if entity_type not in {"agent", "skill"} or not isinstance(entity_id, str) or not entity_id:
        return None

    suggestion = row.get("suggestion") or row.get("description")
    if not isinstance(suggestion, str) or not suggestion.strip():
        return None

    reason = row.get("reason") or row.get("type") or "instruction_refinement"
    target = row.get("target")
    priority = row.get("priority")
    rank = row.get("rank")
    return Improvement(
        entity_type=entity_type,
        entity_id=entity_id,
        score=normalize_float(row.get("score")),
        priority=str(priority) if isinstance(priority, str) and priority else None,
        reason=str(reason) if isinstance(reason, str) and reason else "instruction_refinement",
        suggestion=suggestion.strip(),
        target=str(target) if isinstance(target, str) and target else None,
        trend=normalize_trend(row.get("trend")),
        baseline_delta=normalize_float(row.get("baseline_delta")),
        evidence_sessions=normalize_evidence_sessions(row.get("evidence_sessions")),
        rank=int(rank) if isinstance(rank, int) else None,
    )


def load_improvements(report: dict[str, Any]) -> list[Improvement]:
    improvements: list[Improvement] = []
    raw_improvements = report.get("improvements")
    if not isinstance(raw_improvements, list):
        raise SystemExit("invalid score report JSON: improvements must be a list")
    if isinstance(raw_improvements, list):
        for row in raw_improvements:
            if isinstance(row, dict):
                improvement = improvement_from_row(row)
                if improvement is not None:
                    improvements.append(improvement)
    return improvements


def load_gap_analysis(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    gap_analysis = report.get("gap_analysis")
    if not isinstance(gap_analysis, dict):
        return {"missing_coverage": [], "repeated_patterns": [], "misfit_agents": []}
    normalized: dict[str, list[dict[str, Any]]] = {}
    for key in ("missing_coverage", "repeated_patterns", "misfit_agents"):
        rows = gap_analysis.get(key)
        normalized[key] = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return normalized


def target_matches(improvement: Improvement, target: str) -> bool:
    normalized = target.strip()
    return normalized in {
        improvement.entity_id,
        f"{improvement.entity_type}:{improvement.entity_id}",
        f"{improvement.entity_type}/{improvement.entity_id}",
    }


def select_improvements(
    improvements: list[Improvement],
    target: str | None,
    max_variants: int,
) -> list[Improvement]:
    if target:
        selected = [item for item in improvements if target_matches(item, target)]
        if not selected:
            raise SystemExit(f"target not found in score report improvements: {target}")
        return selected[:max_variants]
    return improvements[:max_variants]


def source_path_for(improvement: Improvement, registry_root: Path, skills_root: Path) -> Path:
    if improvement.entity_type == "agent":
        return registry_root / improvement.entity_id / "instructions.md"
    if improvement.entity_type == "skill":
        return skills_root / improvement.entity_id / "SKILL.md"
    raise SystemExit(f"unsupported entity type: {improvement.entity_type}")


def ensure_source_exists(improvement: Improvement, source_path: Path) -> None:
    if source_path.exists() and source_path.is_file():
        return
    raise SystemExit(
        f"source profile not found for {improvement.entity_type}:{improvement.entity_id}: {source_path}"
    )


def next_variant_id(base_id: str, variant_root: Path, entity_segment: str) -> tuple[str, Path]:
    candidate_id = base_id
    candidate_dir = variant_root / entity_segment / candidate_id
    suffix = 1
    while candidate_dir.exists():
        candidate_id = f"{base_id}-{suffix:02d}"
        candidate_dir = variant_root / entity_segment / candidate_id
        suffix += 1
    return candidate_id, candidate_dir


def build_variant_plans(
    improvements: list[Improvement],
    registry_root: Path,
    skills_root: Path,
    output_dir: Path,
) -> list[VariantPlan]:
    base_id = timestamp_id()
    used_dirs: set[Path] = set()
    plans: list[VariantPlan] = []
    for index, improvement in enumerate(improvements):
        source_path = source_path_for(improvement, registry_root, skills_root)
        ensure_source_exists(improvement, source_path)
        entity_segment = sanitize_segment(improvement.entity_id)
        variant_id, variant_dir = next_variant_id(
            base_id if index == 0 else f"{base_id}-{index + 1:02d}",
            output_dir,
            entity_segment,
        )
        while variant_dir in used_dirs:
            variant_id = f"{variant_id}-next"
            variant_dir = output_dir / entity_segment / variant_id
        used_dirs.add(variant_dir)
        output_path = variant_dir / source_path.name
        plans.append(
            VariantPlan(
                improvement=improvement,
                source_path=source_path,
                output_path=output_path,
                meta_path=variant_dir / "meta.json",
                variant_id=variant_id,
                variant_dir=variant_dir,
                relative_variant_dir=repo_relative(variant_dir),
                modified_filename=source_path.name,
            )
        )
    return plans


def patch_comment_prefix(filename: str) -> tuple[str, str]:
    if filename.endswith((".md", ".markdown")):
        return "<!--", "-->"
    return "#", ""


def build_patch_text(original: str, improvement: Improvement, variant_id: str, created_at: str, filename: str) -> str:
    start_comment, end_comment = patch_comment_prefix(filename)
    end = f" {end_comment}" if end_comment else ""
    lines = [
        "",
        f"{start_comment} HyperAgent variant patch: {variant_id}{end}",
        f"{start_comment} Created at: {created_at}{end}",
        f"{start_comment} Entity: {improvement.entity_type}:{improvement.entity_id}{end}",
        f"{start_comment} Reason: {improvement.reason}{end}",
        f"{start_comment} Score: {improvement.score if improvement.score is not None else 'unknown'}{end}",
    ]
    if improvement.priority:
        lines.append(f"{start_comment} Priority: {improvement.priority}{end}")
    if improvement.evidence_sessions:
        evidence = ", ".join(improvement.evidence_sessions[:5])
        lines.append(f"{start_comment} Evidence sessions: {evidence}{end}")
    lines.extend(
        [
            f"{start_comment} Improvement suggestion:{end}",
            *[f"{start_comment} {line}{end}" for line in improvement.suggestion.splitlines()],
            f"{start_comment} End HyperAgent variant patch{end}",
            "",
        ]
    )
    separator = "\n" if original.endswith("\n") else "\n\n"
    return original + separator + "\n".join(lines)


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).rstrip() + "\n"
    return text


def llm_prompt_for_profile(original: str, improvement: Improvement) -> str:
    payload = {
        "entity_type": improvement.entity_type,
        "entity_id": improvement.entity_id,
        "score": improvement.score,
        "priority": improvement.priority,
        "reason": improvement.reason,
        "suggestion": improvement.suggestion,
        "target": improvement.target,
        "trend": improvement.trend,
        "baseline_delta": improvement.baseline_delta,
        "evidence_sessions": improvement.evidence_sessions,
    }
    return (
        "Rewrite the complete HyperAgent profile below.\n"
        "Return only the full revised profile text. Do not wrap it in Markdown fences. "
        "Do not append comments about the change. Preserve the profile's format and intent, "
        "but concretely incorporate the improvement signals.\n\n"
        f"Improvement signals:\n{json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)}\n\n"
        f"Current profile:\n{original}"
    )


def generate_profile_with_llm(original: str, improvement: Improvement, client: Any) -> str:
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=12000,
        temperature=0.2,
        system=(
            "You edit agent and skill instruction profiles. Your output must be the complete "
            "replacement file content, with no commentary and no Markdown code fence."
        ),
        messages=[{"role": "user", "content": llm_prompt_for_profile(original, improvement)}],
    )
    chunks: list[str] = []
    for block in response.content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            chunks.append(text)
    revised = strip_code_fence("".join(chunks))
    if not revised.strip():
        raise RuntimeError("Claude returned an empty profile")
    return revised if revised.endswith("\n") else revised + "\n"


def meta_for_plan(
    plan: VariantPlan,
    created_at: str,
    score_source: str,
    llm_requested: bool,
    llm_status: str,
) -> dict[str, Any]:
    improvement = plan.improvement
    return {
        "schema_version": SCHEMA_VERSION,
        "variant_id": plan.variant_id,
        "entity_type": improvement.entity_type,
        "entity_id": improvement.entity_id,
        "strategy": "refine",
        "generation_mode": "llm" if llm_status == "success" else "rule_based",
        "llm_requested": llm_requested,
        "llm_status": llm_status,
        "parent_variant": None,
        "created_at": created_at,
        "score_report_source": score_source,
        "source_score": improvement.score,
        "source_path": repo_relative(plan.source_path),
        "original_path": repo_relative(plan.source_path),
        "source_target": improvement.target,
        "change_reason": improvement.suggestion,
        "suggestions_applied": [improvement.reason],
        "priority": improvement.priority,
        "baseline_delta": improvement.baseline_delta,
        "trend": improvement.trend,
        "evidence_sessions": improvement.evidence_sessions,
        "files_modified": [plan.modified_filename],
        "status": "staged",
    }


def execute_plan(
    plan: VariantPlan,
    created_at: str,
    score_source: str,
    use_llm: bool,
    client: Any | None = None,
) -> dict[str, Any]:
    original = plan.source_path.read_text(encoding="utf-8")
    if use_llm:
        if client is None:
            raise RuntimeError("LLM generation requested but no Anthropic client is available")
        patched = generate_profile_with_llm(original, plan.improvement, client)
        llm_status = "success"
    else:
        patched = build_patch_text(original, plan.improvement, plan.variant_id, created_at, plan.modified_filename)
        llm_status = "not_requested"
    meta = meta_for_plan(plan, created_at, score_source, use_llm, llm_status)
    plan.variant_dir.mkdir(parents=True, exist_ok=False)
    plan.output_path.write_text(patched, encoding="utf-8")
    plan.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return variant_result(plan, written=True)


def variant_result(plan: VariantPlan, written: bool) -> dict[str, Any]:
    improvement = plan.improvement
    return {
        "variant_id": plan.variant_id,
        "entity_type": improvement.entity_type,
        "entity_id": improvement.entity_id,
        "variant_dir": plan.relative_variant_dir,
        "source_path": repo_relative(plan.source_path),
        "variant_file": repo_relative(plan.output_path),
        "meta_file": repo_relative(plan.meta_path),
        "score": improvement.score,
        "reason": improvement.reason,
        "suggestion": improvement.suggestion,
        "written": written,
    }


def gap_slug(row: dict[str, Any], fallback: str) -> str:
    value = row.get("pattern") or row.get("agent") or fallback
    return sanitize_segment(str(value).lower())[:80]


def proposal_dir_for(proposals_dir: Path, suggestion_type: str, row: dict[str, Any], index: int) -> Path:
    return proposals_dir / sanitize_segment(suggestion_type) / f"{index:02d}-{gap_slug(row, suggestion_type)}"


def sessions_markdown(row: dict[str, Any]) -> str:
    sessions = row.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        return "- none captured"
    return "\n".join(f"- {session}" for session in sessions if isinstance(session, str) and session)


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def draft_agent_toml(name: str, description: str) -> str:
    return (
        f"name = {toml_string(name)}\n"
        'model = "gpt-5.4-mini"\n'
        'reasoning_effort = "high"\n'
        f"description = {toml_string(description)}\n"
    )


def draft_agent_instructions(name: str, row: dict[str, Any], source_instructions: str | None = None) -> str:
    pattern = row.get("pattern") or row.get("agent") or name
    intro = f"# {name}\n\nYou are a specialized HyperAgent lane for: {pattern}.\n"
    if source_instructions:
        intro += "\nBase agent behavior to specialize from:\n\n"
        intro += source_instructions.strip()[:4000] + "\n"
    return (
        intro
        + "\n## When to Use\n"
        + f"- Route work here when sessions match `{pattern}`.\n"
        + "- Prefer concrete evidence over broad repository rereads.\n"
        + "- Stop and ask for a replan if the task no longer matches this specialty.\n\n"
        + "## Evidence Sessions\n"
        + sessions_markdown(row)
        + "\n"
    )


def draft_skill_markdown(name: str, row: dict[str, Any]) -> str:
    pattern = row.get("pattern") or name
    return (
        "---\n"
        f"name: {name}\n"
        f"description: Handles repeated HyperAgent instruction pattern: {pattern}\n"
        "---\n\n"
        f"# {name}\n\n"
        f"Use when a session matches `{pattern}`.\n\n"
        "## Workflow\n"
        "1. Identify whether this repeated instruction pattern is present.\n"
        "2. Apply the captured checklist before tool execution.\n"
        "3. Report the exact evidence and stop if the pattern no longer applies.\n\n"
        "## Evidence Sessions\n"
        + sessions_markdown(row)
        + "\n"
    )


def write_gap_proposal(
    suggestion_type: str,
    row: dict[str, Any],
    proposal_dir: Path,
    registry_root: Path,
    dry_run: bool,
) -> dict[str, Any]:
    entity_slug = gap_slug(row, suggestion_type)
    name = f"{entity_slug}-proposal"
    files: list[tuple[Path, str]] = []

    if suggestion_type == "new_agent":
        description = f"Specialized agent draft for {row.get('pattern', entity_slug)}"
        files.append((proposal_dir / "agent.toml", draft_agent_toml(name, description)))
        files.append((proposal_dir / "instructions.md", draft_agent_instructions(name, row)))
    elif suggestion_type == "new_skill_or_hook":
        files.append((proposal_dir / "SKILL.md", draft_skill_markdown(name, row)))
    elif suggestion_type == "new_specialized_agent":
        base_agent = str(row.get("agent") or entity_slug)
        source = registry_root / base_agent / "instructions.md"
        source_text = source.read_text(encoding="utf-8") if source.exists() else None
        description = f"Specialized variant draft based on {base_agent}"
        files.append((proposal_dir / "agent.toml", draft_agent_toml(name, description)))
        files.append((proposal_dir / "instructions.md", draft_agent_instructions(name, row, source_text)))
    else:
        files.append((proposal_dir / "proposal.md", json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n"))

    if not dry_run:
        proposal_dir.mkdir(parents=True, exist_ok=False)
        for path, content in files:
            path.write_text(content, encoding="utf-8")

    return {
        "suggestion_type": suggestion_type,
        "proposal_dir": repo_relative(proposal_dir),
        "files": [repo_relative(path) for path, _ in files],
        "written": not dry_run,
    }


def generate_gap_proposals(
    gap_analysis: dict[str, list[dict[str, Any]]],
    proposals_dir: Path,
    registry_root: Path,
    dry_run: bool,
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    index = 1
    for key, suggestion_type in (
        ("missing_coverage", "new_agent"),
        ("repeated_patterns", "new_skill_or_hook"),
        ("misfit_agents", "new_specialized_agent"),
    ):
        for row in gap_analysis.get(key, []):
            if row.get("suggestion_type") != suggestion_type:
                continue
            proposal_dir = proposal_dir_for(proposals_dir, suggestion_type, row, index)
            proposals.append(write_gap_proposal(suggestion_type, row, proposal_dir, registry_root, dry_run))
            index += 1
    return proposals


def print_text_report(output: dict[str, Any]) -> None:
    action = "Dry-run plan" if output["dry_run"] else "Generated variants"
    print(f"Variant Generator {action} (schema v{output['schema_version']})")
    print(f"Candidates: {output['candidate_count']}")
    for variant in output["variants"]:
        status = "would write" if output["dry_run"] else "wrote"
        print(f"- {status} {variant['entity_type']}:{variant['entity_id']} -> {variant['variant_dir']}")
    if output.get("proposals"):
        print(f"Gap proposals: {len(output['proposals'])}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HyperAgent prompt variants from score reports.")
    parser.add_argument("--input", help="Path to score-report.json. Omit to read JSON from stdin.")
    parser.add_argument("--scores", help="Alias for --input, kept for API-CONTRACT compatibility.")
    parser.add_argument("--target", help="Specific entity id to generate. Also accepts agent:<id> or skill:<id>.")
    parser.add_argument("--max-variants", type=int, default=3, help="Maximum variants to generate.")
    parser.add_argument("--strategy", choices=("auto", "refine"), default="auto", help="Generation strategy.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Variant output directory.")
    parser.add_argument("--proposals-dir", default=str(DEFAULT_PROPOSALS_DIR), help="Gap proposal output directory.")
    parser.add_argument("--registry", default=str(REPO_ROOT / "agent-registry"), help="Agent registry root.")
    parser.add_argument("--skills", default=str(REPO_ROOT / "skills"), help="Skills directory root.")
    parser.add_argument("--dry-run", action="store_true", help="Print the generation plan without writing files.")
    parser.add_argument("--no-llm", action="store_true", help="Use local rule-based variants instead of Claude API generation.")
    parser.add_argument("--llm", action="store_true", help="Compatibility alias; LLM generation is the default.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    args = parser.parse_args(argv)
    if args.input and args.scores:
        parser.error("--input and --scores cannot be used together")
    if args.max_variants < 1:
        parser.error("--max-variants must be >= 1")
    return args


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    use_llm = not args.no_llm
    llm_status = "requested"
    client: Any | None = None
    if use_llm:
        if anthropic is None:
            warn("anthropic SDK is not installed; falling back to --no-llm mode")
            use_llm = False
            llm_status = "sdk_missing_fallback"
        elif not args.dry_run:
            client = anthropic.Anthropic()

    report, score_source = load_score_report(args.input or args.scores)
    validate_score_report(report)
    improvements = load_improvements(report)
    gap_analysis = load_gap_analysis(report)
    selected = select_improvements(improvements, args.target, args.max_variants)

    registry_root = expand_input_path(args.registry)
    skills_root = expand_input_path(args.skills)
    output_dir = expand_input_path(args.output_dir)
    proposals_dir = expand_input_path(args.proposals_dir)
    plans = build_variant_plans(selected, registry_root, skills_root, output_dir)

    created_at = utc_now_iso()
    variants = (
        [variant_result(plan, written=False) for plan in plans]
        if args.dry_run
        else [execute_plan(plan, created_at, score_source, use_llm, client) for plan in plans]
    )
    proposals = generate_gap_proposals(
        gap_analysis,
        proposals_dir / timestamp_id(),
        registry_root,
        args.dry_run,
    )
    output = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": created_at,
        "score_report_source": score_source,
        "output_dir": repo_relative(output_dir),
        "proposals_dir": repo_relative(proposals_dir),
        "dry_run": args.dry_run,
        "strategy": "refine" if args.strategy == "auto" else args.strategy,
        "generation_mode": "llm" if use_llm else "rule_based",
        "llm_requested": not args.no_llm,
        "llm_status": llm_status if not use_llm else ("dry_run" if args.dry_run else "success"),
        "candidate_count": len(variants),
        "variants": variants,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
