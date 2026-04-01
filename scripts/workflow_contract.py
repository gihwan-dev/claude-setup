#!/usr/bin/env python3
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TypeAlias

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_POLICY_PATH = REPO_ROOT / "policy" / "workflow.toml"

TomlDict: TypeAlias = dict[str, object]


def _load_toml(path: Path) -> TomlDict:
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"TOML must decode to a table: {path}")
    return loaded


def _require_table(table: TomlDict, key: str, *, path: Path) -> TomlDict:
    value = table.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing table [{key}] in {path}")
    return value


def _require_str(table: TomlDict, key: str, *, path: Path) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing string '{key}' in {path}")
    return value


def _require_str_list(table: TomlDict, key: str, *, path: Path) -> tuple[str, ...]:
    value = table.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"missing string list '{key}' in {path}")
    return tuple(value)


def _optional_str_map(table: TomlDict, key: str, *, path: Path) -> dict[str, str]:
    value = table.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"invalid optional table [{key}] in {path}")

    parsed: dict[str, str] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, str) or not item_value.strip():
            raise ValueError(f"invalid string map '{key}' in {path}")
        parsed[item_key] = item_value
    return parsed


def load_workflow_policy(path: Path = WORKFLOW_POLICY_PATH) -> TomlDict:
    return _load_toml(path)


WORKFLOW_POLICY = load_workflow_policy()

PUBLIC_SURFACE_POLICY = _require_table(
    WORKFLOW_POLICY,
    "public_surface",
    path=WORKFLOW_POLICY_PATH,
)
PROJECTION_POLICY = _require_table(WORKFLOW_POLICY, "projection", path=WORKFLOW_POLICY_PATH)
CODEX_POLICY = _require_table(WORKFLOW_POLICY, "codex", path=WORKFLOW_POLICY_PATH)
TASK_DOCUMENTS_POLICY = _require_table(
    WORKFLOW_POLICY,
    "task_documents",
    path=WORKFLOW_POLICY_PATH,
)

REQUIRED_HELPER_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY,
    "required_helper_agent_ids",
    path=WORKFLOW_POLICY_PATH,
)
PUBLIC_LONG_RUNNING_SKILLS = _require_str_list(
    PUBLIC_SURFACE_POLICY,
    "long_running",
    path=WORKFLOW_POLICY_PATH,
)
DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY,
    "documentation_only_builtins",
    path=WORKFLOW_POLICY_PATH,
)
DEFAULT_CODEX_REASONING_EFFORT = _require_str(
    CODEX_POLICY,
    "default_reasoning_effort",
    path=WORKFLOW_POLICY_PATH,
)
CODEX_REASONING_EFFORT_OVERRIDES = _optional_str_map(
    CODEX_POLICY,
    "reasoning_effort_overrides",
    path=WORKFLOW_POLICY_PATH,
)
EXPECTED_CODEX_REASONING_EFFORT = DEFAULT_CODEX_REASONING_EFFORT
EXPECTED_CODEX_SANDBOX_BY_AGENT = _optional_str_map(
    CODEX_POLICY,
    "sandbox_overrides",
    path=WORKFLOW_POLICY_PATH,
)
GENERATED_SKILL_MANIFEST_NAME = _require_str(
    TASK_DOCUMENTS_POLICY,
    "generated_skill_manifest_name",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_TASK_YAML_REQUIRED_KEYS = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_task_yaml_required_keys",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_AGENT_ORCHESTRATION_REQUIRED_KEYS = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_agent_orchestration_required_keys",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_AGENT_ORCHESTRATION_STRATEGIES = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_agent_orchestration_strategies",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_AGENT_ORCHESTRATION_MAIN_THREAD_ROLES = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_agent_orchestration_main_thread_roles",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_csv_fanout_orchestration_required_keys",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_EXECUTION_PLAN_SECTION_ORDER = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_execution_plan_section_order",
    path=WORKFLOW_POLICY_PATH,
)
BUNDLE_EXECUTION_PLAN_SLICE_REQUIRED_FIELDS = _require_str_list(
    TASK_DOCUMENTS_POLICY,
    "bundle_execution_plan_slice_required_fields",
    path=WORKFLOW_POLICY_PATH,
)


def expected_reasoning_effort_for(agent_id: str) -> str:
    return CODEX_REASONING_EFFORT_OVERRIDES.get(agent_id, DEFAULT_CODEX_REASONING_EFFORT)


__all__ = [
    "BUNDLE_AGENT_ORCHESTRATION_MAIN_THREAD_ROLES",
    "BUNDLE_AGENT_ORCHESTRATION_REQUIRED_KEYS",
    "BUNDLE_AGENT_ORCHESTRATION_STRATEGIES",
    "BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS",
    "BUNDLE_EXECUTION_PLAN_SECTION_ORDER",
    "BUNDLE_EXECUTION_PLAN_SLICE_REQUIRED_FIELDS",
    "BUNDLE_TASK_YAML_REQUIRED_KEYS",
    "CODEX_REASONING_EFFORT_OVERRIDES",
    "DEFAULT_CODEX_REASONING_EFFORT",
    "DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS",
    "EXPECTED_CODEX_REASONING_EFFORT",
    "EXPECTED_CODEX_SANDBOX_BY_AGENT",
    "GENERATED_SKILL_MANIFEST_NAME",
    "PUBLIC_LONG_RUNNING_SKILLS",
    "PUBLIC_SURFACE_POLICY",
    "PROJECTION_POLICY",
    "REPO_ROOT",
    "REQUIRED_HELPER_AGENT_IDS",
    "TASK_DOCUMENTS_POLICY",
    "WORKFLOW_POLICY",
    "WORKFLOW_POLICY_PATH",
    "expected_reasoning_effort_for",
    "load_workflow_policy",
]
