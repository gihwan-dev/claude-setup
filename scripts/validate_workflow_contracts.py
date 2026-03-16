#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    BLOCKING_TIMEOUT_PATH,
    CORE_HELPER_ORCHESTRATION_EXPECTED,
    detect_task_document_mode,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    decide_slice_execution_mode,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    expected_reasoning_effort_for,
    FALLBACK_REQUIRES_ACK,
    HelperCloseSnapshot,
    IMMEDIATE_STATUS_CHECK_POLICY,
    INVALID_CLOSE_REASON,
    NON_CANCEL_STATUS_PING_MODE,
    PLAN_SECTION_ORDER,
    REQUIRED_HELPER_AGENT_IDS,
    SliceExecutionPlan,
    SLICE_BUDGET_ENFORCEMENT,
    SLICE_BUDGET_MAX_NET_LOC,
    SLICE_BUDGET_MAX_REPO_FILES,
    SPEC_VALIDATION_SECTION_ORDER,
    STATUS_PING_DELIVERY,
    STATUS_SECTION_ORDER,
    SYNTHETIC_INTERRUPT_REASON,
    TASK_BUNDLE_CORE_DOCS,
    TASK_BUNDLE_DELIVERY_STRATEGIES,
    TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    TASK_BUNDLE_IMPACT_FLAGS,
    TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS,
    TASK_BUNDLE_TRACEABILITY_IDS,
    TASK_BUNDLE_UI_FIRST_FLAGS,
    TASK_BUNDLE_UI_FIRST_WORK_TYPES,
    TASK_BUNDLE_WORK_TYPES,
    decide_task_bundle_delivery_strategy,
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

    for path in sorted(registry_root.glob("*/agent.toml")):
        data = _load_toml(path)
        agent_id = data.get("id")
        role = data.get("role")
        projection = data.get("projection")
        if not isinstance(agent_id, str) or not isinstance(role, str) or not isinstance(projection, dict):
            continue
        if role not in {"implementer", "orchestrator"}:
            continue
        if _is_projected(projection):
            errors.append(f"projected implementer/orchestrator is not allowed: {path}")


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
        expected_effort = expected_reasoning_effort_for(agent_id)
        if reasoning_effort != expected_effort:
            errors.append(
                f"registry reasoning_effort mismatch for {agent_id}: "
                f"expected={expected_effort!r} actual={reasoning_effort!r} ({path})"
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


def _expect_substrings(path: Path, substrings: tuple[str, ...], errors: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for substring in substrings:
        if substring not in content:
            errors.append(f"{path}: missing required contract snippet: {substring}")


def _expect_heading_sequence(path: Path, headings: tuple[str, ...], errors: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    actual = [
        line[3:].strip()
        for line in content.splitlines()
        if line.startswith("## ")
    ]
    if tuple(actual) != headings:
        errors.append(f"{path}: UI Planning Packet heading order drifted")


def _validate_structure_reviewer_instruction_drift(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    reviewer_path = registry_root / "structure-reviewer" / "instructions.md"

    _expect_substrings(
        reviewer_path,
        (
            "component/view file: target <= 220 LOC, hard limit 300",
            "hook/composable/middleware file: target <= 150 LOC, hard limit 220",
            "React hook/provider/view-model file: target <= 150 LOC, hard limit 220",
            "service/use-case/controller/repository/util/module file: target <= 200 LOC, hard limit 260",
            "any function/method: target <= 40 LOC, hard limit 60",
            "이미 soft limit를 넘긴 파일에 additive diff를 더하면 `FAIL`이다.",
        ),
        errors,
    )


def _validate_browser_explorer_contract(repo_root: Path, errors: list[str]) -> None:
    registry_root = repo_root / "agent-registry"
    core_path = repo_root / "docs" / "policy" / "00-core.md"
    routing_path = repo_root / "docs" / "policy" / "10-routing.md"
    workflows_path = repo_root / "docs" / "policy" / "20-workflows.md"
    browser_agent_config = registry_root / "browser-explorer" / "agent.toml"
    browser_agent_instructions = registry_root / "browser-explorer" / "instructions.md"
    implement_task_skill_path = repo_root / "skills" / "implement-task" / "SKILL.md"

    if not browser_agent_config.exists():
        errors.append(f"missing browser explorer config: {browser_agent_config}")
        return

    payload = _load_toml(browser_agent_config)
    if payload.get("role") != "explorer":
        errors.append("browser-explorer role must remain explorer")
    if payload.get("source") != "repo-agent":
        errors.append("browser-explorer source must remain repo-agent")

    projection = payload.get("projection")
    if not isinstance(projection, dict):
        errors.append(f"missing [projection]: {browser_agent_config}")
    else:
        if projection.get("repo") is not True or projection.get("codex") is not True:
            errors.append("browser-explorer projection must stay enabled for repo/codex")

    codex = payload.get("codex")
    if not isinstance(codex, dict):
        errors.append(f"missing [codex]: {browser_agent_config}")
    else:
        if codex.get("agent_key") != "browser-explorer":
            errors.append("browser-explorer codex.agent_key drifted")
        if codex.get("config_file") != "browser-explorer.toml":
            errors.append("browser-explorer codex.config_file drifted")
        if codex.get("sandbox_mode") != "danger-full-access":
            errors.append("browser-explorer sandbox_mode must remain danger-full-access")

    _expect_substrings(
        browser_agent_instructions,
        (
            "`playwright-interactive`",
            "`target URL 또는 Electron entry`",
            "`상태: final|preliminary`",
            "자동 실행 금지",
        ),
        errors,
    )

    _expect_substrings(
        implement_task_skill_path,
        (
            "`browser-explorer`",
            "`target URL 또는 Electron entry`",
            "`scenario checklist`",
            "`evidence checklist`",
        ),
        errors,
    )

    _expect_substrings(
        core_path,
        (
            "browser-explorer",
        ),
        errors,
    )

    _expect_substrings(
        workflows_path,
        (
            "browser-explorer",
        ),
        errors,
    )


def _validate_writer_runtime_docs(repo_root: Path, errors: list[str]) -> None:
    workflows_path = repo_root / "docs" / "policy" / "20-workflows.md"
    routing_path = repo_root / "docs" / "policy" / "10-routing.md"
    skill_path = repo_root / "skills" / "implement-task" / "SKILL.md"

    _expect_substrings(
        routing_path,
        (
            "small slices + run-to-boundary",
            "queued-only",
            "split/replan before execution",
            "Immediate status check requires explicit cancel path",
        ),
        errors,
    )

    _expect_substrings(
        workflows_path,
        (
            "small slices + run-to-boundary",
        ),
        errors,
    )

    _expect_substrings(
        skill_path,
        (
            "small slices + run-to-boundary",
            "queued-only",
            "slice implementation -> main focused validation -> commit",
            "split/replan before execution",
        ),
        errors,
    )


def _validate_ui_planning_packet_contract(repo_root: Path, errors: list[str]) -> None:
    ux_spec_headings = (
        "Goal/Audience/Platform",
        "30-Second Understanding Checklist",
        "Visual Direction + Anti-goals",
        "Reference Pack (adopt/avoid)",
        "Glossary + Object Model",
        "Layout/App-shell Contract",
        "Token + Primitive Contract",
        "Screen + Flow Coverage",
        "Implementation Prompt/Handoff",
    )
    behavior_headings = (
        "Interaction Model",
        "Keyboard + Focus Contract",
        "Accessibility Contract",
        "Live Update Semantics",
        "State Matrix + Fixture Strategy",
        "Large-run Degradation Rules",
        "Microcopy + Information Expression Rules",
        "Task-based Approval Criteria",
    )

    figma_less_skill = repo_root / "skills" / "figma-less-ui-design" / "SKILL.md"
    figma_less_prompt = repo_root / "skills" / "figma-less-ui-design" / "agents" / "openai.yaml"
    figma_less_patterns = repo_root / "skills" / "figma-less-ui-design" / "references" / "official-patterns.md"
    figma_less_templates = repo_root / "skills" / "figma-less-ui-design" / "references" / "ui-planning-templates.md"
    reference_pack_skill = repo_root / "skills" / "reference-pack" / "SKILL.md"
    reference_pack_prompt = repo_root / "skills" / "reference-pack" / "agents" / "openai.yaml"
    design_skill = repo_root / "skills" / "design-task" / "SKILL.md"
    design_prompt = repo_root / "skills" / "design-task" / "agents" / "openai.yaml"
    design_reference = repo_root / "skills" / "design-task" / "references" / "task-bundle-rules.md"
    bootstrap_skill = repo_root / "skills" / "bootstrap-project-rules" / "SKILL.md"
    bootstrap_prompt = repo_root / "skills" / "bootstrap-project-rules" / "agents" / "openai.yaml"
    implement_skill = repo_root / "skills" / "implement-task" / "SKILL.md"
    implement_prompt = repo_root / "skills" / "implement-task" / "agents" / "openai.yaml"

    for required_path in (
        figma_less_skill,
        figma_less_prompt,
        figma_less_patterns,
        figma_less_templates,
        reference_pack_skill,
        reference_pack_prompt,
    ):
        if not required_path.exists():
            errors.append(f"missing ui planning contract file: {required_path}")

    if figma_less_skill.exists():
        _expect_substrings(
            figma_less_skill,
            (
                "UI Planning Packet",
                "UX_BEHAVIOR_ACCESSIBILITY.md",
                "30-Second Understanding Checklist",
                "Task-based Approval Criteria",
                "reuse + delta",
                "design system",
                "Figma",
            ),
            errors,
        )
    if figma_less_prompt.exists():
        _expect_substrings(
            figma_less_prompt,
            (
                "UI Planning Packet",
                "UX_SPEC.md",
                "UX_BEHAVIOR_ACCESSIBILITY.md",
                "state matrix",
                "allow_implicit_invocation: false",
            ),
            errors,
        )
    if figma_less_patterns.exists():
        _expect_substrings(
            figma_less_patterns,
            (
                "reuse + delta",
                "adopt",
                "avoid",
                "App-shell",
                "Token + Primitive",
                "Accessibility",
            ),
            errors,
        )
    if figma_less_templates.exists():
        _expect_substrings(figma_less_templates, ux_spec_headings + behavior_headings, errors)

    _expect_substrings(
        reference_pack_skill,
        (
            "DESIGN_REFERENCES/",
            "shortlist.md",
            "manifest.json",
            "5~10개",
            "최소 3개",
            "adopt",
            "avoid",
        ),
        errors,
    )
    _expect_substrings(
        reference_pack_prompt,
        (
            "DESIGN_REFERENCES/",
            "manifest.json",
            "adopt",
            "avoid",
            "allow_implicit_invocation: false",
        ),
        errors,
    )

    _expect_substrings(
        design_skill,
        (
            "reference-pack",
            "figma-less-ui-design",
            "UI Planning Packet",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "reuse + delta",
            "web-researcher",
            "architecture-reviewer",
        ),
        errors,
    )
    _expect_substrings(
        design_prompt,
        (
            "reference-pack",
            "figma-less-ui-design",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "design_references",
        ),
        errors,
    )
    _expect_substrings(
        design_reference,
        (
            "reference-pack",
            "UI Planning Packet",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "Goal/Audience/Platform",
            "Interaction Model",
            "DESIGN_REFERENCES/",
            "reuse + delta",
        ),
        errors,
    )
    _expect_substrings(
        bootstrap_skill,
        (
            "UX_SPEC.md",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "DESIGN_REFERENCES/manifest.json",
            "styling stack",
            "component source",
            "Storybook/screenshot tooling",
            "token source path",
            "do/don't only",
            "UX ownership",
        ),
        errors,
    )
    _expect_substrings(
        bootstrap_prompt,
        (
            "UX_SPEC.md",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "DESIGN_REFERENCES/manifest.json",
            "styling stack",
            "component source",
            "Storybook/screenshot tooling",
            "token source path",
            "do/don't only",
        ),
        errors,
    )
    _expect_substrings(
        implement_skill,
        (
            "UX_SPEC.md",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "DESIGN_REFERENCES/manifest.json",
            "checklist",
            "interaction/a11y/microcopy",
            "keyboard/focus",
            "state matrix/fixture",
            "`browser-explorer`",
            "`target URL 또는 Electron entry`",
            "`scenario checklist`",
            "`evidence checklist`",
        ),
        errors,
    )
    _expect_substrings(
        implement_prompt,
        (
            "UX_SPEC.md",
            "UX_BEHAVIOR_ACCESSIBILITY.md",
            "DESIGN_REFERENCES/manifest.json",
            "keyboard/focus",
            "`browser-explorer`",
            "`target URL 또는 Electron entry`",
            "`scenario checklist`",
            "`evidence checklist`",
        ),
        errors,
    )
    for fixture_path in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "UX_SPEC.md",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "UX_SPEC.md",
    ):
        _expect_heading_sequence(fixture_path, ux_spec_headings, errors)

    for fixture_path in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "UX_BEHAVIOR_ACCESSIBILITY.md",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "UX_BEHAVIOR_ACCESSIBILITY.md",
    ):
        _expect_heading_sequence(fixture_path, behavior_headings, errors)

    for task_yaml_path in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "task.yaml",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "task.yaml",
    ):
        _expect_substrings(
            task_yaml_path,
            (
                "ux: UX_SPEC.md",
                "ux_behavior: UX_BEHAVIOR_ACCESSIBILITY.md",
                "design_references: DESIGN_REFERENCES/manifest.json",
                "- UX_BEHAVIOR_ACCESSIBILITY.md",
                "- DESIGN_REFERENCES/",
            ),
            errors,
        )

    for readme_path in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "README.md",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "README.md",
    ):
        _expect_substrings(
            readme_path,
            (
                "UI Planning Packet",
                "UX Behavior",
                "Design References",
                "SLICE-1",
                "interaction/a11y/microcopy",
                "SLICE-2",
                "state matrix/fixture",
            ),
            errors,
        )

    for spec_path in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "SPEC_VALIDATION.md",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "SPEC_VALIDATION.md",
    ):
        _expect_substrings(
            spec_path,
            (
                "UI Planning Packet",
                "UX_BEHAVIOR_ACCESSIBILITY.md",
                "30-Second Understanding Checklist",
                "Task-based Approval Criteria",
                "DESIGN_REFERENCES/manifest.json",
            ),
            errors,
        )

    for reference_root in (
        repo_root / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "DESIGN_REFERENCES",
        repo_root / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "DESIGN_REFERENCES",
    ):
        shortlist_path = reference_root / "shortlist.md"
        manifest_path = reference_root / "manifest.json"
        curated_path = reference_root / "curated"
        raw_path = reference_root / "raw"
        if not shortlist_path.exists():
            errors.append(f"missing design reference shortlist: {shortlist_path}")
        if not manifest_path.exists():
            errors.append(f"missing design reference manifest: {manifest_path}")
        if not curated_path.is_dir():
            errors.append(f"missing curated reference dir: {curated_path}")
        if not raw_path.is_dir():
            errors.append(f"missing raw reference dir: {raw_path}")
        if manifest_path.exists():
            _expect_substrings(
                manifest_path,
                (
                    "\"file\"",
                    "\"source_url\"",
                    "\"captured_at\"",
                    "\"kind\"",
                    "\"adopt_reason\"",
                    "\"avoid_reason\"",
                ),
                errors,
            )
            try:
                entries = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid design reference manifest JSON: {manifest_path}: {exc}")
            else:
                if not isinstance(entries, list):
                    errors.append(f"design reference manifest must decode to a list: {manifest_path}")
                    continue
                if len(entries) < 3:
                    errors.append(f"design reference manifest must contain at least 3 entries: {manifest_path}")
                adopt_count = 0
                avoid_count = 0
                for entry in entries:
                    if not isinstance(entry, dict):
                        errors.append(f"design reference manifest entry must be an object: {manifest_path}")
                        continue
                    missing_fields = sorted(
                        field
                        for field in (
                            "file",
                            "source_url",
                            "captured_at",
                            "kind",
                            "tags",
                            "adopt_reason",
                            "avoid_reason",
                            "notes",
                        )
                        if field not in entry
                    )
                    if missing_fields:
                        errors.append(
                            f"design reference manifest entry missing fields {missing_fields}: {manifest_path}"
                        )
                    kind = entry.get("kind")
                    if kind == "adopt":
                        adopt_count += 1
                    elif kind == "avoid":
                        avoid_count += 1
                if adopt_count < 2 or avoid_count < 1:
                    errors.append(
                        f"design reference manifest should include at least 2 adopt and 1 avoid entries: {manifest_path}"
                    )
        if curated_path.is_dir() and not list(curated_path.glob("*.svg")):
            errors.append(f"curated reference dir must contain placeholder SVGs: {curated_path}")
        if raw_path.is_dir() and not list(raw_path.glob("*.svg")):
            errors.append(f"raw reference dir must contain placeholder SVGs: {raw_path}")


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


def _validate_policy_functions(repo_root: Path, errors: list[str]) -> None:
    policy = _load_toml(repo_root / "policy" / "workflow.toml")
    helper_close = policy.get("helper_close")
    if not isinstance(helper_close, dict):
        errors.append("policy.workflow.toml missing [helper_close] table")
    else:
        if helper_close.get("non_cancel_status_ping_mode") != NON_CANCEL_STATUS_PING_MODE:
            errors.append("helper_close.non_cancel_status_ping_mode drifted")
        if helper_close.get("status_ping_delivery") != STATUS_PING_DELIVERY:
            errors.append("helper_close.status_ping_delivery drifted")
        if helper_close.get("blocking_timeout_path") != BLOCKING_TIMEOUT_PATH:
            errors.append("helper_close.blocking_timeout_path drifted")
        if helper_close.get("immediate_status_check_policy") != IMMEDIATE_STATUS_CHECK_POLICY:
            errors.append("helper_close.immediate_status_check_policy drifted")
        if helper_close.get("synthetic_interrupt_reason") != SYNTHETIC_INTERRUPT_REASON:
            errors.append("helper_close.synthetic_interrupt_reason drifted")
        if helper_close.get("fallback_requires_ack") != FALLBACK_REQUIRES_ACK:
            errors.append("helper_close.fallback_requires_ack drifted")

    slice_budget = policy.get("slice_budget")
    if not isinstance(slice_budget, dict):
        errors.append("policy.workflow.toml missing [slice_budget] table")
    else:
        if slice_budget.get("max_repo_files") != SLICE_BUDGET_MAX_REPO_FILES:
            errors.append("slice_budget.max_repo_files drifted")
        if slice_budget.get("max_net_loc") != SLICE_BUDGET_MAX_NET_LOC:
            errors.append("slice_budget.max_net_loc drifted")
        if slice_budget.get("enforcement") != SLICE_BUDGET_ENFORCEMENT:
            errors.append("slice_budget.enforcement drifted")

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

    timed_out_running = HelperCloseSnapshot(
        helper_id="explorer",
        blocking_class="advisory",
        result_contract="preliminary-or-final",
        close_protocol="explicit-cancel-or-terminal-close",
        late_result_policy="merge-if-relevant",
        timeout_policy=ADVISORY_TIMEOUT_POLICY,
        runtime_status="running",
        observed=True,
        status_pinged=True,
        wait_timed_out_count=1,
    )
    timed_out_running_decision = decide_helper_close_action(timed_out_running)
    if timed_out_running_decision.close_allowed or timed_out_running_decision.action not in {
        "observe",
        "status-ping",
    }:
        errors.append("wait timeout after non-interrupt status ping must remain observe/status-ping only")

    non_cancel_interrupt = HelperCloseSnapshot(
        helper_id="verification-worker",
        blocking_class="semi-blocking",
        result_contract="final-or-checkpoint",
        close_protocol="explicit-cancel-or-terminal-close",
        late_result_policy="merge-if-relevant",
        timeout_policy="observe-and-status-ping",
        runtime_status="running",
        observed=True,
        status_pinged=True,
        interrupt_sent=True,
    )
    non_cancel_interrupt_decision = decide_helper_close_action(non_cancel_interrupt)
    if non_cancel_interrupt_decision.action != "invalid":
        errors.append("non-cancel interrupt sequence must be rejected")

    premature_fallback = HelperCloseSnapshot(
        helper_id="verification-worker",
        blocking_class="semi-blocking",
        result_contract="final-or-checkpoint",
        close_protocol="explicit-cancel-or-terminal-close",
        late_result_policy="merge-if-relevant",
        timeout_policy="observe-and-status-ping",
        runtime_status="interrupted",
        observed=True,
        status_pinged=True,
        interrupt_sent=True,
        close_reason=SYNTHETIC_INTERRUPT_REASON,
        fallback_requested=True,
    )
    premature_fallback_decision = decide_helper_close_action(premature_fallback)
    if premature_fallback_decision.action != "invalid":
        errors.append("parent fallback before terminal/background ack must be rejected")

    late_checkpoint = HelperCloseSnapshot(
        helper_id="explorer",
        blocking_class="advisory",
        result_contract="preliminary-or-final",
        close_protocol="explicit-cancel-or-terminal-close",
        late_result_policy="merge-if-relevant",
        timeout_policy=ADVISORY_TIMEOUT_POLICY,
        runtime_status="interrupted",
        observed=True,
        status_pinged=True,
        interrupt_sent=True,
        drain_grace_elapsed=True,
        close_reason=SYNTHETIC_INTERRUPT_REASON,
        has_checkpoint=True,
    )
    late_checkpoint_decision = decide_helper_close_action(late_checkpoint)
    if late_checkpoint_decision.action != "allow-close" or not late_checkpoint_decision.accept_late_result:
        errors.append("late checkpoint after drain must remain close ack with merge-if-relevant")

    broad_handoff = SliceExecutionPlan(
        repo_files_planned=2,
        net_loc_planned=80,
        work_labels=("setup", "docs"),
    )
    broad_handoff_decision = decide_slice_execution_mode(broad_handoff)
    if broad_handoff_decision.action != "split-replan" or broad_handoff_decision.execution_allowed:
        errors.append("broad PREP-0 execution must be rejected before slice execution")

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
    if "delivery_strategy" not in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS:
        errors.append("task bundle delivery_strategy key drifted")
    if "feature" not in TASK_BUNDLE_WORK_TYPES or "ops" not in TASK_BUNDLE_WORK_TYPES:
        errors.append("task bundle work types drifted")
    if "workflow_changed" not in TASK_BUNDLE_IMPACT_FLAGS or "high_user_risk" not in TASK_BUNDLE_IMPACT_FLAGS:
        errors.append("task bundle impact flags drifted")
    if set(TASK_BUNDLE_DELIVERY_STRATEGIES) != {"standard", "ui-first"}:
        errors.append("task bundle delivery strategies drifted")
    if "feature" not in TASK_BUNDLE_UI_FIRST_WORK_TYPES or "bugfix" not in TASK_BUNDLE_UI_FIRST_WORK_TYPES:
        errors.append("task bundle ui-first work types drifted")
    if set(TASK_BUNDLE_UI_FIRST_FLAGS) != {"ui_surface_changed", "workflow_changed"}:
        errors.append("task bundle ui-first flags drifted")
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
        "UX_BEHAVIOR_ACCESSIBILITY.md",
        "DESIGN_REFERENCES/",
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

    ui_first_strategy = decide_task_bundle_delivery_strategy(
        "feature",
        ("ui_surface_changed",),
    )
    if ui_first_strategy != "ui-first":
        errors.append("ui-surface feature bundle must derive ui-first delivery strategy")

    standard_strategy = decide_task_bundle_delivery_strategy(
        "ops",
        tuple(),
    )
    if standard_strategy != "standard":
        errors.append("ops bundle must derive standard delivery strategy")

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
    _validate_structure_reviewer_instruction_drift(repo_root, errors)
    _validate_browser_explorer_contract(repo_root, errors)
    _validate_writer_runtime_docs(repo_root, errors)
    _validate_ui_planning_packet_contract(repo_root, errors)
    _validate_generated_projections(repo_root, errors)
    _validate_policy_functions(repo_root, errors)
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
