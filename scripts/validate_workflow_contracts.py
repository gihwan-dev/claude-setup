#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from workflow_contract import (
    CORE_HELPER_ORCHESTRATION_EXPECTED,
    DISABLED_WRITABLE_PROJECTION_AGENT_IDS,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    EXPECTED_CODEX_REASONING_EFFORT,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    FORBIDDEN_CONTRACT_PHRASES,
    INTERNAL_PLANNING_ROLE_IDS,
    PLAN_SECTION_ORDER,
    REQUIRED_CONTRACT_PHRASES,
    REQUIRED_HELPER_AGENT_IDS,
    STATUS_SECTION_ORDER,
    WRITABLE_PROJECTION_AGENT_IDS,
    validate_markdown_sections,
)


def _load_toml(path: Path) -> dict[str, object]:
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"TOML must decode to a table: {path}")
    return loaded


def _is_projected(projection: dict[str, object]) -> bool:
    return projection.get("repo") is True or projection.get("codex") is True


def _validate_agent_projection(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"

    for agent_id in INTERNAL_PLANNING_ROLE_IDS:
        path = registry_root / agent_id / "agent.toml"
        if not path.exists():
            errors.append(f"missing planning-role config: {path}")
            continue
        data = _load_toml(path)
        projection = data.get("projection")
        if not isinstance(projection, dict):
            errors.append(f"missing [projection]: {path}")
            continue
        if projection.get("repo") is not False or projection.get("codex") is not False:
            errors.append(
                f"planning-role projection must be disabled (repo=false,codex=false): {path}"
            )

    for agent_id in REQUIRED_HELPER_AGENT_IDS:
        path = registry_root / agent_id / "agent.toml"
        if not path.exists():
            errors.append(f"missing helper config: {path}")
            continue
        data = _load_toml(path)
        projection = data.get("projection")
        if not isinstance(projection, dict):
            errors.append(f"missing [projection]: {path}")
            continue
        if projection.get("repo") is not True or projection.get("codex") is not True:
            errors.append(
                f"helper projection must be enabled (repo=true,codex=true): {path}"
            )
        repo_cfg = data.get("repo")
        if not isinstance(repo_cfg, dict):
            errors.append(f"helper must define [repo] for Claude projection: {path}")

    for agent_id in DISABLED_WRITABLE_PROJECTION_AGENT_IDS:
        path = registry_root / agent_id / "agent.toml"
        if not path.exists():
            errors.append(f"missing disabled projection config: {path}")
            continue
        data = _load_toml(path)
        projection = data.get("projection")
        if not isinstance(projection, dict):
            errors.append(f"missing [projection]: {path}")
            continue
        if projection.get("repo") is not False or projection.get("codex") is not False:
            errors.append(f"projection must remain disabled for {agent_id}: {path}")

    for path in sorted(registry_root.glob("*/agent.toml")):
        data = _load_toml(path)
        agent_id = data.get("id")
        role = data.get("role")
        projection = data.get("projection")
        if not isinstance(agent_id, str) or not isinstance(role, str) or not isinstance(projection, dict):
            continue
        if agent_id in WRITABLE_PROJECTION_AGENT_IDS:
            continue
        if role not in {"implementer", "orchestrator"}:
            continue
        if _is_projected(projection):
            errors.append(
                "projected implementer/orchestrator is not allowed unless it is the "
                f"`worker`: {path}"
            )


def _validate_helper_orchestration(repo_root: Path, errors: list[str]) -> None:
    for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items():
        path = repo_root / "agent-registry" / agent_id / "agent.toml"
        if not path.exists():
            errors.append(f"missing helper config: {path}")
            continue
        data = _load_toml(path)
        orchestration = data.get("orchestration")
        if not isinstance(orchestration, dict):
            errors.append(f"missing [orchestration]: {path}")
            continue

        for key, expected_value in expected.items():
            actual_value = orchestration.get(key)
            if actual_value != expected_value:
                errors.append(
                    f"invalid orchestration mapping for {agent_id}.{key}: "
                    f"expected={expected_value!r} actual={actual_value!r} ({path})"
                )


def _validate_generated_codex_helpers(repo_root: Path, errors: list[str]) -> None:
    managed_config_path = repo_root / "dist" / "codex" / "config.managed-agents.toml"
    if not managed_config_path.exists():
        errors.append(f"missing generated managed config: {managed_config_path}")
        return

    data = _load_toml(managed_config_path)
    agents = data.get("agents")
    if not isinstance(agents, dict):
        errors.append(f"missing [agents] table: {managed_config_path}")
        return

    dist_root = repo_root / "dist" / "codex"
    for agent_id in REQUIRED_HELPER_AGENT_IDS:
        entry = agents.get(agent_id)
        if not isinstance(entry, dict):
            errors.append(f"missing generated helper agent key: agents.{agent_id}")
            continue

        config_file = entry.get("config_file")
        if not isinstance(config_file, str) or not config_file.strip():
            errors.append(f"missing generated config_file for agents.{agent_id}")
            continue

        profile_path = dist_root / config_file
        if not profile_path.exists():
            errors.append(f"missing generated helper profile: {profile_path}")
            continue

        try:
            profile = _load_toml(profile_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        expected_sandbox = EXPECTED_CODEX_SANDBOX_BY_AGENT.get(agent_id, "read-only")
        sandbox_mode = profile.get("sandbox_mode")
        if sandbox_mode != expected_sandbox:
            errors.append(
                f"invalid sandbox_mode for agents.{agent_id}: "
                f"expected={expected_sandbox!r} actual={sandbox_mode!r} ({profile_path})"
            )

        reasoning_effort = profile.get("model_reasoning_effort")
        if reasoning_effort != EXPECTED_CODEX_REASONING_EFFORT:
            errors.append(
                f"invalid model_reasoning_effort for agents.{agent_id}: "
                f"expected={EXPECTED_CODEX_REASONING_EFFORT!r} actual={reasoning_effort!r} ({profile_path})"
            )

    for agent_id, entry in agents.items():
        if not isinstance(agent_id, str) or not isinstance(entry, dict):
            continue
        if agent_id in DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS:
            errors.append(
                f"documentation-only built-in must not be repo-managed: agents.{agent_id}"
            )
            continue
        config_file = entry.get("config_file")
        if not isinstance(config_file, str) or not config_file.strip():
            continue
        profile_path = dist_root / config_file
        if not profile_path.exists():
            continue
        try:
            profile = _load_toml(profile_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        expected_sandbox = EXPECTED_CODEX_SANDBOX_BY_AGENT.get(agent_id, "read-only")
        sandbox_mode = profile.get("sandbox_mode")
        if sandbox_mode != expected_sandbox:
            errors.append(
                f"projected codex agent sandbox mismatch: agents.{agent_id} "
                f"expected={expected_sandbox!r} actual={sandbox_mode!r} ({profile_path})"
            )


def _validate_documentation_only_builtins(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    for agent_id in DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS:
        if (registry_root / agent_id).exists():
            errors.append(
                f"documentation-only built-in must not have repo-managed registry entry: {registry_root / agent_id}"
            )


def _validate_contract_phrases(repo_root: Path, errors: list[str]) -> None:
    for relative_path, phrases in REQUIRED_CONTRACT_PHRASES.items():
        path = repo_root / relative_path
        if not path.exists():
            errors.append(f"missing required file: {path}")
            continue
        content = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in content:
                errors.append(f"missing contract phrase '{phrase}' in {path}")

    for relative_path, phrases in FORBIDDEN_CONTRACT_PHRASES.items():
        path = repo_root / relative_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase in content:
                errors.append(f"forbidden phrase still present '{phrase}' in {path}")


def _validate_task_documents(repo_root: Path, errors: list[str]) -> None:
    task_roots = (repo_root / "tasks", repo_root / "tests" / "fixtures" / "tasks")
    for task_root in task_roots:
        if not task_root.exists():
            continue
        for plan_path in sorted(task_root.rglob("PLAN.md")):
            plan_error = validate_markdown_sections(plan_path, PLAN_SECTION_ORDER)
            if plan_error is not None:
                errors.append(plan_error)
        for status_path in sorted(task_root.rglob("STATUS.md")):
            status_error = validate_markdown_sections(status_path, STATUS_SECTION_ORDER)
            if status_error is not None:
                errors.append(status_error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate long-running workflow contracts")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path",
    )
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    errors: list[str] = []
    _validate_agent_projection(repo_root, errors)
    _validate_helper_orchestration(repo_root, errors)
    _validate_generated_codex_helpers(repo_root, errors)
    _validate_documentation_only_builtins(repo_root, errors)
    _validate_contract_phrases(repo_root, errors)
    _validate_task_documents(repo_root, errors)

    if errors:
        print("workflow-contract validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("workflow-contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
