#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from sync_agents import _read_agent_entries, _validate_entries
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


def _expect_table(payload: dict[str, object], key: str, *, path: Path) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing table [{key}] in {path}")
    return value


def _expect_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing string: {label}")
    return value


def _expect_str_list(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"invalid string list: {label}")
    return tuple(value)


def _expect_str_map(value: object, *, label: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"invalid string map: {label}")
    parsed: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not item.strip():
            raise ValueError(f"invalid string map entry: {label}")
        parsed[key] = item
    return parsed


def _validate_policy(repo_root: Path, errors: list[str]) -> tuple[str, ...]:
    policy_path = repo_root / "policy" / "workflow.toml"
    try:
        payload = _load_toml(policy_path)
        projection = _expect_table(payload, "projection", path=policy_path)
        codex = _expect_table(payload, "codex", path=policy_path)
        task_documents = _expect_table(payload, "task_documents", path=policy_path)

        required_helpers = _expect_str_list(
            projection.get("required_helper_agent_ids"),
            label="projection.required_helper_agent_ids",
        )
        _expect_str_list(
            projection.get("documentation_only_builtins"),
            label="projection.documentation_only_builtins",
        )
        _expect_str(
            codex.get("default_reasoning_effort"),
            label="codex.default_reasoning_effort",
        )
        _expect_str_map(
            codex.get("reasoning_effort_overrides"),
            label="codex.reasoning_effort_overrides",
        )
        _expect_str_map(
            codex.get("sandbox_overrides"),
            label="codex.sandbox_overrides",
        )
        _expect_str(
            task_documents.get("generated_skill_manifest_name"),
            label="task_documents.generated_skill_manifest_name",
        )
        return required_helpers
    except ValueError as exc:
        errors.append(str(exc))
        return ()


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


def _validate_registry(repo_root: Path, required_helpers: tuple[str, ...], errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    if not registry_root.is_dir():
        errors.append(f"missing agent registry: {registry_root}")
        return

    for agent_id in required_helpers:
        agent_dir = registry_root / agent_id
        config_path = agent_dir / "agent.toml"
        instructions_path = agent_dir / "instructions.md"
        if not config_path.exists():
            errors.append(f"missing helper config: {config_path}")
            continue
        if not instructions_path.exists():
            errors.append(f"missing helper instructions: {instructions_path}")
            continue

        try:
            payload = _load_toml(config_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if payload.get("id") != agent_id:
            errors.append(f"helper id mismatch: {config_path}")

        projection = payload.get("projection")
        if not isinstance(projection, dict):
            errors.append(f"missing [projection]: {config_path}")
            continue
        if projection.get("repo") is not True or projection.get("codex") is not True:
            errors.append(f"helper projection must be enabled for repo/codex: {config_path}")

    try:
        entries = _read_agent_entries(registry_root)
        _validate_entries(entries)
    except ValueError as exc:
        errors.append(f"agent registry validation failed: {exc}")


def _validate_generated_surfaces(
    repo_root: Path,
    required_helpers: tuple[str, ...],
    errors: list[str],
) -> None:
    managed_path = repo_root / "dist" / "codex" / "config.managed-agents.toml"
    try:
        payload = _load_toml(managed_path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    agents = payload.get("agents")
    if not isinstance(agents, dict):
        errors.append(f"missing [agents] table in {managed_path}")
        return

    for agent_id in required_helpers:
        entry = agents.get(agent_id)
        if not isinstance(entry, dict):
            errors.append(f"missing generated helper entry: agents.{agent_id}")
            continue

        config_file = entry.get("config_file")
        if not isinstance(config_file, str) or not config_file.strip():
            errors.append(f"missing config_file for generated helper: agents.{agent_id}")
            continue

        profile_path = repo_root / "dist" / "codex" / config_file
        try:
            _load_toml(profile_path)
        except ValueError as exc:
            errors.append(str(exc))


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
    required_helpers = _validate_policy(repo_root, errors)
    _validate_skills(repo_root, errors)
    _validate_registry(repo_root, required_helpers, errors)
    _validate_generated_surfaces(repo_root, required_helpers, errors)

    if run_sync_checks:
        _run_check_command(repo_root, "sync_agents.py", errors)
        _run_check_command(repo_root, "sync_skills_index.py", errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-validate workflow policy, registry, skills, and generated surfaces"
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
