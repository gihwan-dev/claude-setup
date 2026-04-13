#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from sync_skills_index import _collect_skill_entries


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_toml(path: Path) -> dict[str, object]:
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"TOML must decode to a table: {path}")
    return loaded


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc


def _validate_policy(repo_root: Path, errors: list[str]) -> None:
    policy_path = repo_root / "policy" / "workflow.toml"
    try:
        _load_toml(policy_path)
    except ValueError as exc:
        errors.append(str(exc))


def _validate_hyperagent(repo_root: Path, errors: list[str]) -> None:
    hyperagent_dir = repo_root / "scripts" / "hyperagent"
    hyperagent_policy = repo_root / "policy" / "hyperagent.toml"
    if not hyperagent_dir.exists() and not hyperagent_policy.exists():
        return

    try:
        _load_toml(hyperagent_policy)
    except ValueError as exc:
        errors.append(str(exc))

    required_files = (
        "analyze_sessions.py",
        "score.py",
        "generate_variant.py",
        "archive.py",
        "apply.py",
        "evolve.py",
    )
    for filename in required_files:
        script_path = hyperagent_dir / filename
        if not script_path.is_file():
            errors.append(f"missing hyperagent script: {script_path}")


def _validate_skills(repo_root: Path, errors: list[str]) -> None:
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        errors.append(f"missing skills directory: {skills_root}")
        return

    try:
        _collect_skill_entries(skills_root)
    except ValueError as exc:
        errors.append(f"skill frontmatter validation failed: {exc}")

    manifest_path = skills_root / "manifest.json"
    try:
        payload = _load_json(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    if not isinstance(payload, dict):
        errors.append(f"manifest must decode to an object: {manifest_path}")


def _run_check_command(repo_root: Path, script_name: str, errors: list[str]) -> None:
    script_path = repo_root / "scripts" / script_name
    if not script_path.exists():
        errors.append(f"missing script: {script_path}")
        return

    completed = subprocess.run(
        [sys.executable, str(script_path), "--check"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return

    details = "\n".join(
        part.strip()
        for part in (completed.stdout, completed.stderr)
        if part and part.strip()
    )
    suffix = f"\n{details}" if details else ""
    errors.append(
        f"check command failed: {script_name} --check (exit {completed.returncode}){suffix}"
    )


def validate_repo(repo_root: Path, *, run_sync_checks: bool = True) -> list[str]:
    errors: list[str] = []
    _validate_policy(repo_root, errors)
    _validate_hyperagent(repo_root, errors)
    _validate_skills(repo_root, errors)

    if run_sync_checks:
        _run_check_command(repo_root, "sync_agents.py", errors)
        _run_check_command(repo_root, "sync_skills_index.py", errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-validate policy parsing, skill metadata, and sync drift"
    )
    parser.parse_args(argv)

    errors = validate_repo(_repo_root())
    if errors:
        print("workflow-contract validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("workflow-contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
