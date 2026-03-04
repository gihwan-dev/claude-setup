#!/usr/bin/env python3
"""
Choose the best documentation folder for the current repository.

Usage:
    python3 scripts/find_doc_target.py [repo_root]

Output (JSON):
    {
      "target_path": "...",
      "target_kind": "docs" | "root",
      "reason": "...",
      "candidate_count": 2
    }
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

DOC_DIR_NAMES = {"docs", "doc", "documentation", "guide", "guides"}
IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".turbo",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "vendor",
    "tmp",
}
MAX_SCAN_DEPTH = 4


def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def resolve_repo_root(start_path: Path) -> Path:
    code, output = run_git(["rev-parse", "--show-toplevel"], start_path)
    if code == 0 and output:
        return Path(output).resolve()
    return start_path.resolve()


def parse_changed_paths(repo_root: Path) -> list[str]:
    code, output = run_git(["status", "--porcelain"], repo_root)
    if code != 0 or not output:
        return []

    changed: list[str] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue

        # "XY path" or rename format "XY old -> new"
        entry = line[3:].strip()
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1].strip()
        if entry:
            changed.append(entry)
    return changed


def walk_doc_candidates(repo_root: Path, max_depth: int = MAX_SCAN_DEPTH) -> list[Path]:
    candidates: list[Path] = []
    root_depth = len(repo_root.parts)

    for current_root, dir_names, _ in os.walk(repo_root):
        current = Path(current_root)
        depth = len(current.parts) - root_depth

        dir_names[:] = [
            name
            for name in dir_names
            if name not in IGNORED_DIR_NAMES and not name.startswith(".")
        ]

        if depth > max_depth:
            dir_names[:] = []
            continue

        if current.name.lower() in DOC_DIR_NAMES:
            candidates.append(current)
            dir_names[:] = []

    return candidates


def contains_markdown(path: Path) -> bool:
    for pattern in ("*.md", "*.mdx"):
        if next(path.rglob(pattern), None) is not None:
            return True
    return False


def relative_posix(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def compute_score(
    candidate: Path,
    repo_root: Path,
    changed_paths: Iterable[str],
) -> tuple[int, list[str]]:
    rel_path = relative_posix(candidate, repo_root)
    rel_parts = Path(rel_path).parts
    changed_list = list(changed_paths)

    score = 0
    reasons: list[str] = []

    if contains_markdown(candidate):
        score += 8
        reasons.append("contains markdown files")

    if rel_path == "docs":
        score += 4
        reasons.append("standard top-level docs folder")
    if rel_path == "packages/docs":
        score += 6
        reasons.append("common monorepo docs package")

    depth_bonus = max(0, 5 - len(rel_parts))
    if depth_bonus > 0:
        score += depth_bonus

    if changed_list:
        if any(path == rel_path or path.startswith(rel_path + "/") for path in changed_list):
            score += 30
            reasons.append("already touched by current changes")

        candidate_scope = rel_parts[0] if rel_parts else ""
        if candidate_scope and any(
            Path(path).parts and Path(path).parts[0] == candidate_scope
            for path in changed_list
        ):
            score += 10
            reasons.append("shares top-level scope with changed files")

    if not reasons:
        reasons.append("best available docs directory by heuristic")

    return score, reasons


def choose_target(repo_root: Path) -> dict[str, object]:
    changed_paths = parse_changed_paths(repo_root)
    candidates = walk_doc_candidates(repo_root)

    if not candidates:
        return {
            "target_path": str(repo_root),
            "target_kind": "root",
            "reason": "No documentation directory found; fallback to repository root.",
            "candidate_count": 0,
        }

    scored: list[tuple[int, int, str, Path, list[str]]] = []
    for candidate in candidates:
        score, reasons = compute_score(candidate, repo_root, changed_paths)
        rel = relative_posix(candidate, repo_root)
        depth = len(Path(rel).parts)
        scored.append((score, depth, rel, candidate, reasons))

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    best_score, _, _, best_path, reasons = scored[0]
    reason_text = "; ".join(reasons)

    return {
        "target_path": str(best_path),
        "target_kind": "docs",
        "reason": f"Selected docs directory with score {best_score}: {reason_text}.",
        "candidate_count": len(candidates),
    }


def main() -> int:
    input_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    repo_root = resolve_repo_root(input_root)
    result = choose_target(repo_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
