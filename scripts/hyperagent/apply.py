#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
HYPERAGENT_DIR = Path(__file__).resolve().parent
IMPROVEMENT_LOG = HYPERAGENT_DIR / "improvement-log.jsonl"
ARCHIVE_SCRIPT = HYPERAGENT_DIR / "archive.py"
PROPOSALS_DIR = HYPERAGENT_DIR / "proposals"
SCHEMA_VERSION = "1"


class ApplyError(Exception):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_repo_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def load_json_object(path: Path, description: str) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ApplyError(f"{description} not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ApplyError(f"invalid {description} JSON: {exc}") from None
    if not isinstance(loaded, dict):
        raise ApplyError(f"invalid {description} JSON: top-level value must be an object")
    return loaded


def ensure_within_repo(path: Path, description: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        raise ApplyError(f"{description} must be inside repo: {path}") from None
    return resolved


def run_command(command: list[str], description: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if result.returncode != 0:
        detail = output["stderr"] or output["stdout"]
        raise ApplyError(f"{description} failed: {detail}", code=2)
    return output


def select_variant_from_archive(entity_id: str) -> tuple[Path, dict[str, Any]]:
    result = run_command(
        [sys.executable, repo_relative(ARCHIVE_SCRIPT), "select", "--entity", entity_id, "--json"],
        "archive select",
    )
    try:
        output = json.loads(str(result["stdout"]))
    except json.JSONDecodeError as exc:
        raise ApplyError(f"invalid archive select JSON: {exc}", code=2) from None
    if not isinstance(output, dict) or not isinstance(output.get("selected"), dict):
        raise ApplyError("archive select JSON did not include selected variant", code=2)
    selected = output["selected"]
    variant_dir = selected.get("variant_dir")
    if not isinstance(variant_dir, str) or not variant_dir:
        raise ApplyError("archive selected record did not include variant_dir", code=2)
    return resolve_repo_path(variant_dir), selected


def load_variant_dir(args: argparse.Namespace) -> tuple[Path, dict[str, Any] | None]:
    if args.from_archive:
        if not args.entity:
            raise ApplyError("--entity is required with --from-archive")
        return select_variant_from_archive(args.entity)
    if not args.variant_dir:
        raise ApplyError("provide --variant-dir or --from-archive --entity")
    return resolve_repo_path(args.variant_dir), None


def validate_meta(meta: dict[str, Any], variant_dir: Path) -> None:
    for field in ("variant_id", "entity_type", "entity_id"):
        if not isinstance(meta.get(field), str) or not meta.get(field):
            raise ApplyError(f"invalid meta.json: missing required field: {field}")
    if meta["entity_type"] not in {"agent", "skill"}:
        raise ApplyError(f"invalid meta.json: unsupported entity_type: {meta['entity_type']}")
    if not (variant_dir / "meta.json").is_file():
        raise ApplyError(f"meta.json not found: {variant_dir / 'meta.json'}")


def target_from_meta(meta: dict[str, Any]) -> Path:
    entity_type = str(meta["entity_type"])
    entity_id = str(meta["entity_id"])
    source_target = meta.get("source_target") or meta.get("source_path") or meta.get("original_path")
    if isinstance(source_target, str) and source_target:
        candidate = Path(source_target)
        if entity_type == "agent" and len(candidate.parts) == 3:
            if candidate.parts[0] == "agent-registry" and candidate.parts[2] == "instructions.md":
                return REPO_ROOT / candidate
        if entity_type == "skill" and len(candidate.parts) >= 3:
            if candidate.parts[0] == "skills" and candidate.parts[-1] == "SKILL.md":
                return REPO_ROOT / candidate
    if entity_type == "agent":
        return REPO_ROOT / "agent-registry" / entity_id / "instructions.md"
    return REPO_ROOT / "skills" / entity_id / "SKILL.md"


def payload_from_variant(meta: dict[str, Any], variant_dir: Path, target_path: Path) -> Path:
    expected_name = target_path.name
    payload = variant_dir / expected_name
    if not payload.is_file():
        raise ApplyError(f"variant payload not found: {payload}")
    return payload


def determine_tier(meta: dict[str, Any], target_path: Path) -> tuple[int, str]:
    if not target_path.exists():
        return 3, "new_creation"
    if meta["entity_type"] == "agent":
        return 1, "agent_profile_update"
    return 2, "skill_prompt_update"


def action_for_tier(tier: int, approve: bool) -> str:
    if tier == 2:
        return "apply_observe"
    if tier == 3 and not approve:
        return "pending"
    return "apply"


def git_status_for(path: Path) -> str:
    result = run_command(["git", "status", "--porcelain", "--", repo_relative(path)], "git status")
    return str(result["stdout"])


def assert_target_clean(target_path: Path) -> None:
    if target_path.exists() and git_status_for(target_path):
        raise ApplyError(f"target has uncommitted changes: {repo_relative(target_path)}", code=2)


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    variant_dir, archive_record = load_variant_dir(args)
    variant_dir = ensure_within_repo(variant_dir, "variant directory")
    if not variant_dir.is_dir():
        raise ApplyError(f"variant directory not found: {variant_dir}")

    meta = load_json_object(variant_dir / "meta.json", "meta.json")
    validate_meta(meta, variant_dir)
    target_path = ensure_within_repo(target_from_meta(meta), "target path")
    payload_path = ensure_within_repo(payload_from_variant(meta, variant_dir, target_path), "variant payload")
    tier, tier_reason = determine_tier(meta, target_path)
    action = action_for_tier(tier, args.approve)
    proposal_path = PROPOSALS_DIR / f"{meta['entity_id']}-{meta['variant_id']}.json" if action == "pending" else None

    commands: list[list[str]] = []
    if action != "pending":
        commands = [
            ["git", "add", repo_relative(target_path)],
            ["git", "commit", "-m", f"[hyperagent] apply {meta['entity_id']} {meta['variant_id']}"],
            [sys.executable, "scripts/sync_agents.py"],
            [sys.executable, "scripts/install_assets.py", "--link"],
        ]

    return {
        "schema_version": SCHEMA_VERSION,
        "dry_run": args.dry_run,
        "from_archive": bool(args.from_archive),
        "archive_record": archive_record,
        "variant_id": meta["variant_id"],
        "entity_type": meta["entity_type"],
        "entity_id": meta["entity_id"],
        "variant_dir": repo_relative(variant_dir),
        "payload_path": repo_relative(payload_path),
        "target_path": repo_relative(target_path),
        "tier": tier,
        "tier_reason": tier_reason,
        "action": action,
        "approved": bool(args.approve),
        "proposal_path": repo_relative(proposal_path) if proposal_path is not None else None,
        "observation_sessions": 3 if tier == 2 and action != "pending" else 0,
        "commands": commands,
        "status": "planned",
    }


def append_log(event: dict[str, Any]) -> None:
    IMPROVEMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with IMPROVEMENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def save_proposal(plan: dict[str, Any]) -> dict[str, Any]:
    proposal_path = plan.get("proposal_path")
    if not isinstance(proposal_path, str) or not proposal_path:
        raise ApplyError("pending plan did not include proposal_path")
    path = ensure_within_repo(REPO_ROOT / proposal_path, "proposal path")
    path.parent.mkdir(parents=True, exist_ok=True)
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "proposal_pending",
        "timestamp": utc_now_iso(),
        "plan": plan,
    }
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_log(
        {
            "schema_version": SCHEMA_VERSION,
            "event_type": "pending",
            "timestamp": proposal["timestamp"],
            "variant_id": plan["variant_id"],
            "entity_type": plan["entity_type"],
            "entity_id": plan["entity_id"],
            "tier": plan["tier"],
            "action": plan["action"],
            "proposal_path": proposal_path,
            "status": "pending",
        }
    )
    return {**plan, "status": "pending", "proposal_saved": proposal_path}


def apply_plan(plan: dict[str, Any]) -> dict[str, Any]:
    payload_path = REPO_ROOT / str(plan["payload_path"])
    target_path = REPO_ROOT / str(plan["target_path"])
    assert_target_clean(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(payload_path, target_path)

    add_result = run_command(["git", "add", repo_relative(target_path)], "git add")
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", repo_relative(target_path)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if diff_result.returncode == 0:
        raise ApplyError(f"no SSOT changes to commit for {repo_relative(target_path)}", code=2)
    if diff_result.returncode not in {0, 1}:
        raise ApplyError(f"git diff failed: {diff_result.stderr.strip()}", code=2)

    commit_message = f"[hyperagent] apply {plan['entity_id']} {plan['variant_id']}"
    commit_result = run_command(["git", "commit", "-m", commit_message], "git commit")
    commit_hash = run_command(["git", "rev-parse", "HEAD"], "git rev-parse")["stdout"]
    sync_result = run_command([sys.executable, "scripts/sync_agents.py"], "sync_agents.py")
    install_result = run_command([sys.executable, "scripts/install_assets.py", "--link"], "install_assets.py")

    timestamp = utc_now_iso()
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "applied",
        "timestamp": timestamp,
        "variant_id": plan["variant_id"],
        "entity_type": plan["entity_type"],
        "entity_id": plan["entity_id"],
        "variant_dir": plan["variant_dir"],
        "target_path": plan["target_path"],
        "tier": plan["tier"],
        "action": plan["action"],
        "commit_hash": commit_hash,
        "observation_sessions": plan["observation_sessions"],
        "status": "applied",
    }
    append_log(event)
    return {
        **plan,
        "status": "applied",
        "commit_hash": commit_hash,
        "git_add": add_result,
        "git_commit": commit_result,
        "sync_result": sync_result,
        "install_result": install_result,
        "log_event": event,
    }


def commit_subject(commit_hash: str) -> str:
    result = run_command(["git", "show", "-s", "--format=%s", commit_hash], "git show")
    return str(result["stdout"])


def rollback_commit(args: argparse.Namespace) -> dict[str, Any]:
    subject = commit_subject(args.rollback)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": args.dry_run,
        "rollback": args.rollback,
        "tier": None,
        "action": "rollback",
        "target_path": None,
        "commit_subject": subject,
        "status": "planned",
    }
    if not subject.startswith("[hyperagent]"):
        raise ApplyError(f"rollback commit is not a hyperagent improvement: {args.rollback}", code=2)
    if args.dry_run:
        return plan

    revert_result = run_command(["git", "revert", "--no-edit", args.rollback], "git revert")
    revert_commit_hash = run_command(["git", "rev-parse", "HEAD"], "git rev-parse")["stdout"]
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "rollback",
        "timestamp": utc_now_iso(),
        "rolled_back_commit": args.rollback,
        "revert_commit_hash": revert_commit_hash,
        "commit_subject": subject,
        "status": "rolled_back",
    }
    append_log(event)
    return {
        **plan,
        "status": "rolled_back",
        "revert_commit_hash": revert_commit_hash,
        "git_revert": revert_result,
        "log_event": event,
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    if args.rollback:
        return rollback_commit(args)
    plan = build_plan(args)
    if args.dry_run:
        return plan
    if plan["action"] == "pending":
        return save_proposal(plan)
    return apply_plan(plan)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a HyperAgent variant to the SSOT.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--variant-dir", help="Variant directory containing meta.json and payload file.")
    source.add_argument("--from-archive", action="store_true", help="Select the best variant from archive.py.")
    source.add_argument("--rollback", help="Revert a previous [hyperagent] improvement commit.")
    parser.add_argument("--entity", help="Entity id for --from-archive.")
    parser.add_argument("--approve", action="store_true", help="Approve Tier 3 application.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing files or running pipeline commands.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON.")
    return parser.parse_args(argv)


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        output = execute(args)
    except ApplyError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(exc), "status": "error"}, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)
        return exc.code
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(output)
    return 0


def print_text(output: dict[str, Any]) -> None:
    if output.get("action") == "rollback":
        print(f"Rollback {output['status']}: {output['rollback']}")
        return
    print(f"{output['action']}: {output['entity_id']} {output['variant_id']}")
    print(f"tier: {output['tier']}")
    print(f"target_path: {output['target_path']}")
    print(f"status: {output['status']}")


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
