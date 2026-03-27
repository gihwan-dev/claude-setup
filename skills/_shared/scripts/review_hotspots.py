#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MIN_CHANGED_FILES = 2
DEFAULT_MIN_TOTAL_DIFF_LOC = 150
DEFAULT_MAX_HOTSPOT_PATHS = 3
DEFAULT_POLICY_RELATIVE_PATH = Path("policy") / "workflow.toml"

_EXCLUDED_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "cargo.lock",
}
_EXCLUDED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".snap",
}
_EXCLUDED_SEGMENTS = {
    ".git",
    ".next",
    ".turbo",
    ".yarn",
    "coverage",
    "dist",
    "build",
    "node_modules",
}


@dataclass(frozen=True)
class HotspotPolicy:
    min_changed_files: int = DEFAULT_MIN_CHANGED_FILES
    min_total_diff_loc: int = DEFAULT_MIN_TOTAL_DIFF_LOC
    max_hotspot_paths: int = DEFAULT_MAX_HOTSPOT_PATHS


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    deleted: int

    @property
    def changed_lines(self) -> int:
        return self.added + self.deleted


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _normalize_rename_path(path: str) -> str:
    normalized = path.strip()
    brace_pattern = re.compile(r"\{([^{}]+) => ([^{}]+)\}")
    while True:
        match = brace_pattern.search(normalized)
        if match is None:
            break
        normalized = (
            f"{normalized[:match.start()]}"
            f"{match.group(2)}"
            f"{normalized[match.end():]}"
        )
    if " => " in normalized:
        normalized = normalized.rsplit(" => ", 1)[1]
    return normalized.strip()


def _is_maintainability_candidate(path: str) -> bool:
    normalized = path.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if lowered.endswith(".min.js") or lowered.endswith(".min.css"):
        return False

    pure_path = Path(normalized)
    if pure_path.name.lower() in _EXCLUDED_FILENAMES:
        return False
    if pure_path.suffix.lower() in _EXCLUDED_SUFFIXES:
        return False
    if any(segment.lower() in _EXCLUDED_SEGMENTS for segment in pure_path.parts):
        return False
    return True


def _change_from_mapping(item: dict[str, Any]) -> FileChange:
    path = str(item.get("path", "")).strip()
    changed_lines = _safe_int(item.get("changed_lines"))
    added = _safe_int(item.get("added"))
    deleted = _safe_int(item.get("deleted"))
    if changed_lines and not added and not deleted:
        added = changed_lines
    return FileChange(
        path=_normalize_rename_path(path),
        added=added,
        deleted=deleted,
    )


def parse_numstat(text: str) -> list[FileChange]:
    changes: list[FileChange] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = raw_line.split("\t", 2)
        if len(parts) != 3:
            continue
        raw_added, raw_deleted, raw_path = parts
        if raw_added == "-" or raw_deleted == "-":
            continue
        change = FileChange(
            path=_normalize_rename_path(raw_path),
            added=_safe_int(raw_added),
            deleted=_safe_int(raw_deleted),
        )
        if change.path:
            changes.append(change)
    return changes


def parse_json_payload(text: str) -> list[FileChange]:
    payload = json.loads(text)
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = payload.get("files", [])
    else:
        raise ValueError("classifier JSON input must be a list or an object with a 'files' key")

    if not isinstance(entries, list):
        raise ValueError("classifier JSON 'files' value must be a list")

    changes: list[FileChange] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("classifier JSON entries must be objects")
        change = _change_from_mapping(entry)
        if change.path:
            changes.append(change)
    return changes


def _discover_policy_file(policy_root: Path | None = None) -> Path | None:
    if policy_root is not None:
        resolved = policy_root.resolve()
        if resolved.is_file():
            return resolved if resolved.suffix == ".toml" else None
        search_root = resolved
    else:
        search_root = Path.cwd().resolve()

    current = search_root
    while True:
        candidate = current / DEFAULT_POLICY_RELATIVE_PATH
        if candidate.exists():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def load_hotspot_policy(policy_root: Path | None = None) -> HotspotPolicy:
    policy_path = _discover_policy_file(policy_root)
    if policy_path is None:
        return HotspotPolicy()

    try:
        payload = tomllib.loads(policy_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return HotspotPolicy()

    review_triggers = payload.get("review_triggers")
    if not isinstance(review_triggers, dict):
        return HotspotPolicy()

    return HotspotPolicy(
        min_changed_files=_safe_int(
            review_triggers.get(
                "structure_review_min_changed_files",
                DEFAULT_MIN_CHANGED_FILES,
            )
        )
        or DEFAULT_MIN_CHANGED_FILES,
        min_total_diff_loc=_safe_int(
            review_triggers.get(
                "structure_review_min_diff_loc",
                DEFAULT_MIN_TOTAL_DIFF_LOC,
            )
        )
        or DEFAULT_MIN_TOTAL_DIFF_LOC,
        max_hotspot_paths=DEFAULT_MAX_HOTSPOT_PATHS,
    )


def classify_review_scope(
    changes: list[FileChange],
    *,
    policy: HotspotPolicy | None = None,
) -> dict[str, object]:
    active_policy = policy or HotspotPolicy()
    eligible_changes = [
        change
        for change in changes
        if change.changed_lines > 0 and _is_maintainability_candidate(change.path)
    ]
    total_changed_files = len(eligible_changes)
    total_diff_loc = sum(change.changed_lines for change in eligible_changes)

    if (
        total_changed_files < active_policy.min_changed_files
        or total_diff_loc < active_policy.min_total_diff_loc
    ):
        return {
            "review_mode": "diff-only",
            "hotspot_paths": [],
            "overflow_hotspot_paths": [],
            "maintainability_reasons": [],
        }

    ranked_changes = sorted(
        eligible_changes,
        key=lambda change: (-change.changed_lines, change.path),
    )
    selected = ranked_changes[: active_policy.max_hotspot_paths]
    overflow = ranked_changes[active_policy.max_hotspot_paths :]
    hotspot_paths = [change.path for change in selected]
    overflow_paths = [change.path for change in overflow]

    reasons = [
        (
            "diff crossed hotspot threshold: "
            f"{total_changed_files} files / {total_diff_loc} changed lines"
        ),
        f"selected hotspot files: {', '.join(hotspot_paths)}",
    ]
    if overflow_paths:
        reasons.append(
            f"{len(overflow_paths)} additional hotspot candidates omitted by cap"
        )

    return {
        "review_mode": "diff+full-file-hotspots",
        "hotspot_paths": hotspot_paths,
        "overflow_hotspot_paths": overflow_paths,
        "maintainability_reasons": reasons,
    }


def _read_input(path: str | None) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify changed files into diff-only or diff+full-file-hotspots "
            "for multi-review maintainability passes."
        )
    )
    parser.add_argument(
        "--input-format",
        choices=("numstat", "json"),
        default="numstat",
        help="Input format. `numstat` expects `git diff --numstat` output.",
    )
    parser.add_argument(
        "--input-file",
        default="-",
        help="Input file path. Defaults to stdin.",
    )
    parser.add_argument(
        "--policy-root",
        help=(
            "Optional directory or TOML file used to discover policy/workflow.toml. "
            "Defaults to walking upward from the current working directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_input = _read_input(args.input_file).strip()
    policy_root = Path(args.policy_root).resolve() if args.policy_root else None

    try:
        if raw_input:
            if args.input_format == "json":
                changes = parse_json_payload(raw_input)
            else:
                changes = parse_numstat(raw_input)
        else:
            changes = []
        result = classify_review_scope(
            changes,
            policy=load_hotspot_policy(policy_root),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON input: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


__all__ = [
    "DEFAULT_MAX_HOTSPOT_PATHS",
    "DEFAULT_MIN_CHANGED_FILES",
    "DEFAULT_MIN_TOTAL_DIFF_LOC",
    "FileChange",
    "HotspotPolicy",
    "classify_review_scope",
    "load_hotspot_policy",
    "parse_json_payload",
    "parse_numstat",
]


if __name__ == "__main__":
    raise SystemExit(main())
