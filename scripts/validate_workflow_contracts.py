#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from sync_agents import (
    _format_codex_agent_toml,
    _format_managed_config,
    _format_repo_markdown,
    _read_agent_entries,
    _validate_entries,
)
from workflow_contract import (
    ADVISORY_TIMEOUT_POLICY,
    AdvisorySliceContext,
    AGENT_CONTRACTS_BY_ID,
    CORE_HELPER_ORCHESTRATION_EXPECTED,
    detect_task_document_mode,
    DISABLED_WRITABLE_PROJECTION_AGENT_IDS,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    EXPECTED_CODEX_REASONING_EFFORT,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    HelperCloseSnapshot,
    INVALID_CLOSE_REASON,
    INTERNAL_PLANNING_ROLE_IDS,
    PLAN_SECTION_ORDER,
    REQUIRED_HELPER_AGENT_IDS,
    SPEC_VALIDATION_SECTION_ORDER,
    STATUS_SECTION_ORDER,
    TASK_BUNDLE_CORE_DOCS,
    TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    TASK_BUNDLE_IMPACT_FLAGS,
    TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS,
    TASK_BUNDLE_TRACEABILITY_IDS,
    TASK_BUNDLE_WORK_TYPES,
    WRITABLE_PROJECTION_AGENT_IDS,
    decide_spec_validation_gate,
    decide_helper_close_action,
    derive_task_bundle_required_docs,
    should_spawn_advisory_helper,
    validate_legacy_task_root,
    validate_markdown_sections,
    validate_task_bundle_root,
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


def _validate_registry_codex_contract(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    for agent_id in REQUIRED_HELPER_AGENT_IDS:
        path = registry_root / agent_id / "agent.toml"
        if not path.exists():
            continue
        data = _load_toml(path)
        codex = data.get("codex")
        if not isinstance(codex, dict):
            errors.append(f"missing [codex]: {path}")
            continue

        reasoning_effort = codex.get("reasoning_effort")
        if reasoning_effort != EXPECTED_CODEX_REASONING_EFFORT:
            errors.append(
                f"registry reasoning_effort mismatch for {agent_id}: "
                f"expected={EXPECTED_CODEX_REASONING_EFFORT!r} actual={reasoning_effort!r} ({path})"
            )

        expected_sandbox = EXPECTED_CODEX_SANDBOX_BY_AGENT.get(agent_id, "read-only")
        sandbox_mode = codex.get("sandbox_mode")
        if sandbox_mode != expected_sandbox:
            errors.append(
                f"registry sandbox_mode mismatch for {agent_id}: "
                f"expected={expected_sandbox!r} actual={sandbox_mode!r} ({path})"
            )


def _validate_helper_orchestration(errors: list[str]) -> None:
    required_keys = {
        "blocking_class",
        "result_contract",
        "close_protocol",
        "late_result_policy",
        "timeout_policy",
        "allowed_close_reasons",
    }
    for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items():
        contract = AGENT_CONTRACTS_BY_ID.get(agent_id)
        if contract is None:
            errors.append(f"missing helper contract: {agent_id}")
            continue
        orchestration = contract.get("orchestration")
        if not isinstance(orchestration, dict):
            errors.append(f"missing [orchestration] for {agent_id}")
            continue

        missing_keys = required_keys - set(orchestration.keys())
        if missing_keys:
            errors.append(
                f"helper orchestration missing keys for {agent_id}: {sorted(missing_keys)}"
            )

        if orchestration != expected:
            errors.append(f"helper orchestration cache drifted for {agent_id}")


def _validate_generated_projections(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    entries = _read_agent_entries(registry_root)
    try:
        _validate_entries(entries)
    except ValueError as exc:
        errors.append(str(exc))
        return

    agents_dir = repo_root / "agents"
    codex_agents_dir = repo_root / "dist" / "codex" / "agents"
    managed_config_path = repo_root / "dist" / "codex" / "config.managed-agents.toml"

    for entry in entries:
        if entry.repo_projection:
            projected_path = agents_dir / f"{entry.agent_id}.md"
            if not projected_path.exists():
                errors.append(f"missing generated repo projection: {projected_path}")
            else:
                expected_content = _format_repo_markdown(entry)
                actual_content = projected_path.read_text(encoding="utf-8")
                if actual_content != expected_content:
                    errors.append(f"generated repo projection drifted: {projected_path}")

        if entry.codex_projection:
            if not entry.codex_config_file:
                errors.append(f"missing codex config_file in registry for {entry.agent_id}")
                continue
            projected_path = codex_agents_dir / entry.codex_config_file
            if not projected_path.exists():
                errors.append(f"missing generated codex profile: {projected_path}")
            else:
                expected_content = _format_codex_agent_toml(entry)
                actual_content = projected_path.read_text(encoding="utf-8")
                if actual_content != expected_content:
                    errors.append(f"generated codex profile drifted: {projected_path}")

    if not managed_config_path.exists():
        errors.append(f"missing generated managed config: {managed_config_path}")
        return
    expected_managed_config = _format_managed_config(entries)
    actual_managed_config = managed_config_path.read_text(encoding="utf-8")
    if actual_managed_config != expected_managed_config:
        errors.append(f"generated managed config drifted: {managed_config_path}")


def _validate_policy_functions(errors: list[str]) -> None:
    bad_sequence = HelperCloseSnapshot(
        helper_id="explorer",
        blocking_class="advisory",
        result_contract="preliminary-or-final",
        close_protocol="explicit-cancel-or-terminal-close",
        late_result_policy="merge-if-relevant",
        timeout_policy=ADVISORY_TIMEOUT_POLICY,
        runtime_status="running",
        observed=True,
        status_pinged=True,
        wait_timed_out_count=2,
        close_reason=INVALID_CLOSE_REASON,
    )
    bad_sequence_decision = decide_helper_close_action(bad_sequence)
    if bad_sequence_decision.close_allowed or bad_sequence_decision.action == "allow-close":
        errors.append("invalid advisory close sequence was not rejected")
    if not bad_sequence_decision.accept_late_result:
        errors.append("advisory late result policy must remain merge-if-relevant")

    quiet_slice = AdvisorySliceContext(helper_id="code-quality-reviewer", can_change_current_decision=True)
    if should_spawn_advisory_helper(quiet_slice):
        errors.append("small/low-risk slice should not spawn advisory reviewer")

    risky_slice = AdvisorySliceContext(
        helper_id="code-quality-reviewer",
        files_changed=3,
        can_change_current_decision=True,
    )
    if not should_spawn_advisory_helper(risky_slice):
        errors.append("triggered advisory reviewer was not selected by spawn gate")

    if "task.yaml" not in TASK_BUNDLE_CORE_DOCS:
        errors.append("task bundle core docs must include task.yaml")
    if "task" not in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS or "required_docs" not in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS:
        errors.append("task bundle task.yaml required keys drifted")
    if "success_criteria" not in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS or "major_boundaries" not in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS:
        errors.append("task bundle continuity keys drifted")
    if "feature" not in TASK_BUNDLE_WORK_TYPES or "ops" not in TASK_BUNDLE_WORK_TYPES:
        errors.append("task bundle work types drifted")
    if "workflow_changed" not in TASK_BUNDLE_IMPACT_FLAGS or "high_user_risk" not in TASK_BUNDLE_IMPACT_FLAGS:
        errors.append("task bundle impact flags drifted")
    if TASK_BUNDLE_TRACEABILITY_IDS.get("risk_prefix") != "RISK":
        errors.append("task bundle traceability ids drifted")
    if TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER != (
        "Execution slices",
        "Verification",
        "Stop / Replan conditions",
    ):
        errors.append("task bundle execution plan section order drifted")

    feature_docs = derive_task_bundle_required_docs(
        "feature",
        ("ui_surface_changed", "architecture_significant"),
    )
    required_feature_docs = {
        "README.md",
        "EXECUTION_PLAN.md",
        "SPEC_VALIDATION.md",
        "STATUS.md",
        "PRD.md",
        "UX_SPEC.md",
        "TECH_SPEC.md",
        "ACCEPTANCE.feature",
        "ADRs/",
    }
    if not required_feature_docs.issubset(set(feature_docs)):
        errors.append("feature bundle required docs derivation drifted")

    bugfix_docs = derive_task_bundle_required_docs(
        "bugfix",
        ("high_user_risk",),
    )
    if "REGRESSION.md" not in bugfix_docs:
        errors.append("bugfix high-risk bundle must require REGRESSION.md")

    contract_docs = derive_task_bundle_required_docs(
        "feature",
        ("public_contract_changed", "data_contract_changed"),
    )
    if "openapi.yaml" not in contract_docs or "schema.json" not in contract_docs:
        errors.append("contract-changing bundle must require openapi.yaml and schema.json defaults")

    advisory_gate = decide_spec_validation_gate(tuple(), ("README.md", "EXECUTION_PLAN.md", "STATUS.md"))
    if advisory_gate != "advisory":
        errors.append("low-risk bundle should default to advisory validation gate")

    blocking_gate = decide_spec_validation_gate(
        ("workflow_changed",),
        ("README.md", "EXECUTION_PLAN.md", "STATUS.md"),
    )
    if blocking_gate != "blocking":
        errors.append("workflow_changed must force blocking validation gate")


def _validate_documentation_only_builtins(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    managed_config_path = repo_root / "dist" / "codex" / "config.managed-agents.toml"
    managed_agents: dict[str, object] = {}
    if managed_config_path.exists():
        managed_data = _load_toml(managed_config_path)
        agents = managed_data.get("agents")
        if isinstance(agents, dict):
            managed_agents = agents

    for agent_id in DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS:
        if (registry_root / agent_id).exists():
            errors.append(
                f"documentation-only built-in must not have repo-managed registry entry: {registry_root / agent_id}"
            )
        if agent_id in managed_agents:
            errors.append(
                f"documentation-only built-in must not be repo-managed: agents.{agent_id}"
            )


def _validate_task_documents(repo_root: Path, errors: list[str]) -> None:
    task_roots = (repo_root / "tasks", repo_root / "tests" / "fixtures" / "tasks")
    for task_root in task_roots:
        if not task_root.exists():
            continue
        for candidate in sorted(path for path in task_root.iterdir() if path.is_dir()):
            mode = detect_task_document_mode(candidate)
            if mode is None:
                continue
            if mode == "mixed":
                errors.append(f"{candidate}: mixed task mode is not allowed")
                continue
            if mode == "invalid":
                errors.append(f"{candidate}: task directory must contain task.yaml or PLAN.md")
                continue
            if mode == "bundle":
                errors.extend(validate_task_bundle_root(candidate))
                continue
            errors.extend(validate_legacy_task_root(candidate))


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
    _validate_registry_codex_contract(repo_root, errors)
    _validate_helper_orchestration(errors)
    _validate_generated_projections(repo_root, errors)
    _validate_policy_functions(errors)
    _validate_documentation_only_builtins(repo_root, errors)
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
