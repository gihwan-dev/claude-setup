#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PATH = Path(__file__).resolve().with_name("archive.jsonl")
PRUNED_STATUSES = {"pruned", "deleted"}
UNSELECTABLE_STATUSES = {"pruned", "deleted", "rejected"}


class ArchiveError(Exception):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def resolve_input_path(raw_path: str) -> Path:
    path = expand_input_path(raw_path)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def sanitize_segment(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._/-]+", "-", value).strip("/.-")
    sanitized = sanitized.replace("/", "-")
    return sanitized or "unknown"


def load_json_object(path: Path, description: str) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ArchiveError(f"{description} not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"invalid {description} JSON: {exc}") from None
    if not isinstance(loaded, dict):
        raise ArchiveError(f"invalid {description} JSON: top-level value must be an object")
    return loaded


def ensure_archive_file() -> None:
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PATH.touch(exist_ok=True)


def load_events() -> list[dict[str, Any]]:
    if not ARCHIVE_PATH.exists():
        ensure_archive_file()
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(ARCHIVE_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ArchiveError(f"invalid archive.jsonl line {line_number}: {exc}", code=2) from None
        if not isinstance(event, dict):
            raise ArchiveError(f"invalid archive.jsonl line {line_number}: expected object", code=2)
        events.append(event)
    return events


def append_event(event: dict[str, Any]) -> None:
    ensure_archive_file()
    with ARCHIVE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def append_events(events: list[dict[str, Any]]) -> None:
    ensure_archive_file()
    with ARCHIVE_PATH.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def normalized_files(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def normalized_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def normalized_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def effective_score(record: dict[str, Any]) -> float | None:
    for key in ("evaluated_score", "score", "source_score"):
        score = normalized_number(record.get(key))
        if score is not None:
            return score
    fitness = record.get("fitness")
    if isinstance(fitness, dict):
        values = [float(value) for value in fitness.values() if isinstance(value, (int, float))]
        if values:
            return sum(values) / len(values)
    return None


def score_for_ordering(record: dict[str, Any]) -> float:
    score = effective_score(record)
    return score if score is not None else 0.0


def timestamp_for_ordering(record: dict[str, Any]) -> str:
    value = record.get("created_at") or record.get("timestamp")
    return str(value) if isinstance(value, str) else ""


def sort_best_first(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: (
            score_for_ordering(record),
            timestamp_for_ordering(record),
            str(record.get("variant_id") or ""),
        ),
        reverse=True,
    )


def materialize_records(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for event in events:
        variant_id = event.get("variant_id")
        if not isinstance(variant_id, str) or not variant_id:
            continue
        event_type = str(event.get("event_type") or "add")
        if event_type in {"add", "record"}:
            if variant_id not in records:
                record = dict(event)
                record["status"] = str(record.get("status") or "archived")
                score = effective_score(record)
                if score is not None:
                    record["score"] = score
                records[variant_id] = record
        elif event_type == "status_change" and variant_id in records:
            record = records[variant_id]
            record["status"] = str(event.get("new_status") or record.get("status") or "")
            if normalized_number(event.get("evaluated_score")) is not None:
                record["evaluated_score"] = float(event["evaluated_score"])
                record["score"] = float(event["evaluated_score"])
            record["updated_at"] = event.get("timestamp")
        elif event_type == "prune" and variant_id in records:
            record = records[variant_id]
            record["status"] = "pruned"
            record["pruned_at"] = event.get("timestamp")
            record["prune_reason"] = event.get("reason")
            record["updated_at"] = event.get("timestamp")
    return list(records.values())


def current_records() -> list[dict[str, Any]]:
    return materialize_records(load_events())


def validate_variant_meta(meta: dict[str, Any], variant_dir: Path) -> None:
    required = ("variant_id", "entity_type", "entity_id")
    missing = [field for field in required if not isinstance(meta.get(field), str) or not meta.get(field)]
    if missing:
        raise ArchiveError(f"invalid meta.json: missing required field(s): {', '.join(missing)}")
    if meta["entity_type"] not in {"agent", "skill"}:
        raise ArchiveError(f"invalid meta.json: unsupported entity_type: {meta['entity_type']}")
    if not (variant_dir / "meta.json").is_file():
        raise ArchiveError(f"meta.json not found: {variant_dir / 'meta.json'}")


def archive_tag(entity_id: str, variant_id: str) -> str:
    return f"archive/{sanitize_segment(entity_id)}/{sanitize_segment(variant_id)}"


def git_tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "tag", "--list", tag],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ArchiveError(f"git tag lookup failed: {result.stderr.strip()}", code=2)
    return result.stdout.strip() == tag


def create_git_tag(tag: str) -> bool:
    if git_tag_exists(tag):
        return False
    result = subprocess.run(
        ["git", "tag", tag],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ArchiveError(f"git tag creation failed for {tag}: {result.stderr.strip()}", code=2)
    return True


def build_add_record(args: argparse.Namespace, variant_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    evaluated_score = normalized_number(args.score)
    source_score = normalized_number(meta.get("source_score"))
    score = evaluated_score if evaluated_score is not None else source_score
    status = args.status or str(meta.get("status") or "archived")
    tag = None if args.no_tag else args.tag or archive_tag(meta["entity_id"], meta["variant_id"])
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "add",
        "timestamp": utc_now_iso(),
        "variant_id": meta["variant_id"],
        "entity_type": meta["entity_type"],
        "entity_id": meta["entity_id"],
        "strategy": meta.get("strategy"),
        "parent_variant": meta.get("parent_variant"),
        "created_at": meta.get("created_at"),
        "source_score": source_score,
        "evaluated_score": evaluated_score,
        "score": score,
        "status": status,
        "files": normalized_files(meta.get("files_modified")),
        "suggestions_applied": normalized_strings(meta.get("suggestions_applied")),
        "evidence_sessions": normalized_strings(meta.get("evidence_sessions")),
        "behavioral_tags": normalized_strings(meta.get("behavioral_tags")),
        "variant_dir": repo_relative(variant_dir),
        "meta_path": repo_relative(variant_dir / "meta.json"),
        "source_path": meta.get("source_path"),
        "original_path": meta.get("original_path"),
        "change_summary": meta.get("change_summary") or meta.get("change_reason"),
        "git_tag": tag,
    }
    return {key: value for key, value in record.items() if value is not None}


def command_add(args: argparse.Namespace) -> dict[str, Any]:
    variant_dir = resolve_input_path(args.variant_dir)
    if not variant_dir.is_dir():
        raise ArchiveError(f"variant directory not found: {variant_dir}")
    meta = load_json_object(variant_dir / "meta.json", "meta.json")
    validate_variant_meta(meta, variant_dir)
    records = current_records()
    existing = next((record for record in records if record.get("variant_id") == meta["variant_id"]), None)
    if existing is not None:
        return {
            "schema_version": SCHEMA_VERSION,
            "archive_path": repo_relative(ARCHIVE_PATH),
            "added": False,
            "git_tag_created": False,
            "record": existing,
        }

    record = build_add_record(args, variant_dir, meta)
    tag_created = False
    if record.get("git_tag"):
        tag_created = create_git_tag(str(record["git_tag"]))
    append_event(record)
    return {
        "schema_version": SCHEMA_VERSION,
        "archive_path": repo_relative(ARCHIVE_PATH),
        "added": True,
        "git_tag_created": tag_created,
        "record": record,
    }


def filtered_records(args: argparse.Namespace) -> list[dict[str, Any]]:
    records = current_records()
    if args.entity:
        records = [record for record in records if record.get("entity_id") == args.entity]
    if args.status:
        records = [record for record in records if record.get("status") == args.status]
    if not getattr(args, "include_pruned", False):
        records = [record for record in records if record.get("status") not in PRUNED_STATUSES]
    return records


def command_list(args: argparse.Namespace) -> dict[str, Any]:
    records = sort_best_first(filtered_records(args))
    return {
        "schema_version": SCHEMA_VERSION,
        "archive_path": repo_relative(ARCHIVE_PATH),
        "count": len(records),
        "records": records,
    }


def command_select(args: argparse.Namespace) -> dict[str, Any]:
    records = filtered_records(args)
    records = [record for record in records if record.get("status") not in UNSELECTABLE_STATUSES]
    if not records:
        raise ArchiveError(f"variant not found for entity: {args.entity}")
    selected = sort_best_first(records)[0]
    return {
        "schema_version": SCHEMA_VERSION,
        "archive_path": repo_relative(ARCHIVE_PATH),
        "entity_id": args.entity,
        "selected": selected,
    }


def prune_candidates(records: list[dict[str, Any]], max_per_entity: int, max_total: int, min_score: float | None) -> list[dict[str, Any]]:
    eligible = [record for record in records if record.get("status") not in PRUNED_STATUSES]
    protected = {str(record.get("variant_id")) for record in eligible if record.get("status") == "applied"}
    selected_for_prune: dict[str, dict[str, Any]] = {}

    by_entity: dict[str, list[dict[str, Any]]] = {}
    for record in eligible:
        entity_id = str(record.get("entity_id") or "")
        by_entity.setdefault(entity_id, []).append(record)

    for entity_records in by_entity.values():
        candidates = [record for record in sort_best_first(entity_records) if str(record.get("variant_id")) not in protected]
        for record in candidates[max_per_entity:]:
            selected_for_prune[str(record["variant_id"])] = record

    remaining = [
        record
        for record in sort_best_first(eligible)
        if str(record.get("variant_id")) not in selected_for_prune
    ]
    removable_remaining = [record for record in remaining if str(record.get("variant_id")) not in protected]
    keep_remaining = [record for record in remaining if str(record.get("variant_id")) in protected]
    overflow = max(len(keep_remaining) + len(removable_remaining) - max_total, 0)
    if overflow:
        for record in list(reversed(removable_remaining))[:overflow]:
            selected_for_prune[str(record["variant_id"])] = record

    if min_score is not None:
        for record in eligible:
            if str(record.get("variant_id")) in protected:
                continue
            if score_for_ordering(record) < min_score:
                selected_for_prune[str(record["variant_id"])] = record

    return sort_best_first(list(selected_for_prune.values()))


def command_prune(args: argparse.Namespace) -> dict[str, Any]:
    records = current_records()
    candidates = prune_candidates(records, args.max_per_entity, args.max_total, args.min_score)
    timestamp = utc_now_iso()
    events = [
        {
            "schema_version": SCHEMA_VERSION,
            "event_type": "prune",
            "timestamp": timestamp,
            "variant_id": record["variant_id"],
            "entity_type": record.get("entity_type"),
            "entity_id": record.get("entity_id"),
            "score": effective_score(record),
            "status": "pruned",
            "reason": "archive_limit",
            "git_tag": record.get("git_tag"),
        }
        for record in candidates
    ]
    if not args.dry_run and events:
        append_events(events)
    return {
        "schema_version": SCHEMA_VERSION,
        "archive_path": repo_relative(ARCHIVE_PATH),
        "dry_run": args.dry_run,
        "max_per_entity": args.max_per_entity,
        "max_total": args.max_total,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "events": events,
    }


def print_text(output: dict[str, Any]) -> None:
    if "record" in output:
        record = output["record"]
        verb = "Added" if output.get("added") else "Already archived"
        print(f"{verb}: {record.get('entity_id')} {record.get('variant_id')}")
    elif "selected" in output:
        selected = output["selected"]
        print(f"Selected: {selected.get('entity_id')} {selected.get('variant_id')} score={effective_score(selected)}")
    elif "candidate_count" in output:
        print(f"Prune candidates: {output['candidate_count']}")
        for record in output["candidates"]:
            print(f"- {record.get('entity_id')} {record.get('variant_id')} score={effective_score(record)}")
    else:
        print(f"Archive records: {output.get('count', 0)}")
        for record in output.get("records", []):
            print(f"- {record.get('entity_id')} {record.get('variant_id')} status={record.get('status')} score={effective_score(record)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage HyperAgent variant archive records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Register a variant directory in archive.jsonl.")
    add.add_argument("--variant-dir", required=True, help="Variant directory containing meta.json.")
    add.add_argument("--score", type=float, help="Evaluated score for this variant.")
    add.add_argument("--status", choices=("staged", "evaluated", "applied", "archived", "rejected"), help="Archive status.")
    add.add_argument("--tag", help="Git tag name to create.")
    add.add_argument("--no-tag", action="store_true", help="Do not create a Git tag.")
    add.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    add.set_defaults(func=command_add)

    list_parser = subparsers.add_parser("list", help="List archive records.")
    list_parser.add_argument("--entity", help="Filter by entity id.")
    list_parser.add_argument("--status", help="Filter by current status.")
    list_parser.add_argument("--include-pruned", action="store_true", help="Include pruned records.")
    list_parser.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    list_parser.set_defaults(func=command_list)

    select = subparsers.add_parser("select", help="Select the highest-scoring variant for an entity.")
    select.add_argument("--entity", required=True, help="Entity id to select for.")
    select.add_argument("--status", help="Filter by current status before selecting.")
    select.add_argument("--include-pruned", action="store_true", help="Include pruned records before status exclusion.")
    select.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    select.set_defaults(func=command_select)

    prune = subparsers.add_parser("prune", help="Mark archive records over retention limits as pruned.")
    prune.add_argument("--max-per-entity", type=int, default=5, help="Maximum retained variants per entity.")
    prune.add_argument("--max-total", type=int, default=50, help="Maximum retained variants overall.")
    prune.add_argument("--min-score", type=float, help="Prune non-applied variants below this score.")
    prune.add_argument("--dry-run", action="store_true", help="Print prune plan without writing archive events.")
    prune.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    prune.set_defaults(func=command_prune)

    args = parser.parse_args(argv)
    if args.command == "prune":
        if args.max_per_entity < 1:
            parser.error("--max-per-entity must be >= 1")
        if args.max_total < 1:
            parser.error("--max-total must be >= 1")
    return args


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        output = args.func(args)
    except ArchiveError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
