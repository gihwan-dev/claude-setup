#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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


def _require_str_list(
    table: dict[str, object],
    key: str,
    *,
    path: Path,
    errors: list[str],
) -> list[str]:
    value = table.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"missing string list '{key}' in {path}")
        return []
    return value


def _yaml_has_top_level_key(text: str, key: str) -> bool:
    pattern = rf"(?m)^{re.escape(key)}:\s*(?:.*)?$"
    return re.search(pattern, text) is not None


def _yaml_top_level_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if match is None:
        return None
    return match.group(1).strip().strip('"').strip("'")


def _yaml_child_lines(text: str, parent_key: str) -> list[str]:
    lines = text.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line.strip() == f"{parent_key}:":
            start_index = index + 1
            break
    if start_index is None:
        return []

    child_lines: list[str] = []
    for line in lines[start_index:]:
        if line and not line.startswith(" "):
            break
        child_lines.append(line)
    return child_lines


def _yaml_child_keys(text: str, parent_key: str) -> set[str]:
    keys: set[str] = set()
    for line in _yaml_child_lines(text, parent_key):
        match = re.match(r"^  ([A-Za-z0-9_]+):(?:\s+.*)?$", line)
        if match:
            keys.add(match.group(1))
    return keys


def _yaml_child_scalar(text: str, parent_key: str, child_key: str) -> str | None:
    for line in _yaml_child_lines(text, parent_key):
        match = re.match(rf"^  {re.escape(child_key)}:\s*(.+?)\s*$", line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return None


def _extract_markdown_section(text: str, heading: str) -> str:
    pattern = rf"(?ms)^# {re.escape(heading)}\n(.*?)(?=^# |\Z)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _validate_execution_plan_order(
    text: str,
    section_order: list[str],
    *,
    path: Path,
    errors: list[str],
) -> None:
    positions: list[int] = []
    for heading in section_order:
        match = re.search(rf"(?m)^# {re.escape(heading)}$", text)
        if match is None:
            errors.append(f"missing execution-plan heading '{heading}' in {path}")
            return
        positions.append(match.start())
    if positions != sorted(positions):
        errors.append(f"execution-plan headings out of order in {path}")


def _validate_execution_plan_slices(
    text: str,
    required_fields: list[str],
    *,
    strategy: str | None,
    main_thread_role: str | None,
    path: Path,
    errors: list[str],
) -> None:
    execution_body = _extract_markdown_section(text, "Execution slices")
    if not execution_body.strip():
        errors.append(f"missing execution slices body in {path}")
        return

    slice_matches = list(
        re.finditer(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", execution_body)
    )
    if not slice_matches:
        errors.append(f"missing slice entries in {path}")
        return

    for slice_match in slice_matches:
        slice_name = slice_match.group(1).strip()
        slice_body = slice_match.group(2)
        fields: dict[str, str] = {}
        for line in slice_body.splitlines():
            field_match = re.match(r"^- ([^:]+):\s*(.*)$", line)
            if field_match:
                fields[field_match.group(1).strip()] = field_match.group(2).strip()

        for field in required_fields:
            if field not in fields:
                errors.append(f"missing slice field '{field}' in {path} ({slice_name})")

        if strategy == "manager":
            orchestration_value = fields.get("Orchestration", "").lower()
            if "manager" not in orchestration_value:
                errors.append(
                    f"manager bundle slice must declare manager orchestration in {path} ({slice_name})"
                )

        if main_thread_role == "synthesize-control-only":
            allowed_actions = fields.get("Allowed main-thread actions", "").lower()
            if "direct implementation" in allowed_actions or "direct validation" in allowed_actions:
                errors.append(
                    f"forbidden main-thread action leaked into {path} ({slice_name})"
                )


def _validate_fixture_task_bundle(
    task_dir: Path,
    task_contract: dict[str, list[str]],
    *,
    errors: list[str],
) -> None:
    task_yaml_path = task_dir / "task.yaml"
    execution_plan_path = task_dir / "EXECUTION_PLAN.md"
    if not task_yaml_path.exists() or not execution_plan_path.exists():
        return

    task_text = task_yaml_path.read_text(encoding="utf-8")
    for key in task_contract["task_yaml_required_keys"]:
        if not _yaml_has_top_level_key(task_text, key):
            errors.append(f"missing task.yaml key '{key}' in {task_yaml_path}")

    if _yaml_has_top_level_key(task_text, "agent_orchestration"):
        child_keys = _yaml_child_keys(task_text, "agent_orchestration")
        for key in task_contract["agent_orchestration_required_keys"]:
            if key not in child_keys:
                errors.append(
                    f"missing agent_orchestration key '{key}' in {task_yaml_path}"
                )
    else:
        child_keys = set()

    strategy = _yaml_child_scalar(task_text, "agent_orchestration", "strategy")
    main_thread_role = _yaml_child_scalar(task_text, "agent_orchestration", "main_thread_role")

    if strategy and strategy not in task_contract["agent_orchestration_strategies"]:
        errors.append(f"invalid agent_orchestration.strategy '{strategy}' in {task_yaml_path}")
    if main_thread_role and main_thread_role not in task_contract["agent_orchestration_main_thread_roles"]:
        errors.append(
            f"invalid agent_orchestration.main_thread_role '{main_thread_role}' in {task_yaml_path}"
        )

    execution_topology = _yaml_top_level_scalar(task_text, "execution_topology")
    if execution_topology in {"csv-fanout", "hybrid"} and not _yaml_has_top_level_key(task_text, "orchestration"):
        errors.append(
            f"missing row-level orchestration block for execution_topology={execution_topology} in {task_yaml_path}"
        )

    execution_plan_text = execution_plan_path.read_text(encoding="utf-8")
    _validate_execution_plan_order(
        execution_plan_text,
        task_contract["execution_plan_section_order"],
        path=execution_plan_path,
        errors=errors,
    )
    _validate_execution_plan_slices(
        execution_plan_text,
        task_contract["execution_plan_slice_required_fields"],
        strategy=strategy,
        main_thread_role=main_thread_role,
        path=execution_plan_path,
        errors=errors,
    )


def _validate_task_bundle_contracts(repo_root: Path, errors: list[str]) -> None:
    policy_path = repo_root / "policy" / "workflow.toml"
    try:
        policy = _load_toml(policy_path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    task_documents = policy.get("task_documents")
    if not isinstance(task_documents, dict):
        errors.append(f"missing table [task_documents] in {policy_path}")
        return

    task_contract = {
        "task_yaml_required_keys": _require_str_list(
            task_documents,
            "bundle_task_yaml_required_keys",
            path=policy_path,
            errors=errors,
        ),
        "agent_orchestration_required_keys": _require_str_list(
            task_documents,
            "bundle_agent_orchestration_required_keys",
            path=policy_path,
            errors=errors,
        ),
        "agent_orchestration_strategies": _require_str_list(
            task_documents,
            "bundle_agent_orchestration_strategies",
            path=policy_path,
            errors=errors,
        ),
        "agent_orchestration_main_thread_roles": _require_str_list(
            task_documents,
            "bundle_agent_orchestration_main_thread_roles",
            path=policy_path,
            errors=errors,
        ),
        "execution_plan_section_order": _require_str_list(
            task_documents,
            "bundle_execution_plan_section_order",
            path=policy_path,
            errors=errors,
        ),
        "execution_plan_slice_required_fields": _require_str_list(
            task_documents,
            "bundle_execution_plan_slice_required_fields",
            path=policy_path,
            errors=errors,
        ),
    }

    fixtures_root = repo_root / "tests" / "fixtures" / "tasks"
    if not fixtures_root.is_dir():
        return

    for task_dir in sorted(path for path in fixtures_root.iterdir() if path.is_dir()):
        _validate_fixture_task_bundle(task_dir, task_contract, errors=errors)


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
    _validate_skills(repo_root, errors)
    _validate_task_bundle_contracts(repo_root, errors)

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
