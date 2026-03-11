#!/usr/bin/env python3
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_ROOT = REPO_ROOT / "policy"
WORKFLOW_POLICY_PATH = POLICY_ROOT / "workflow.toml"
AGENT_REGISTRY_ROOT = REPO_ROOT / "agent-registry"

OrchestrationValue: TypeAlias = str | list[str]
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


def _require_str_map(table: TomlDict, key: str, *, path: Path) -> dict[str, str]:
    value = table.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing table [{key}] in {path}")
    parsed: dict[str, str] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, str) or not item_value.strip():
            raise ValueError(f"invalid string map '{key}' in {path}")
        parsed[item_key] = item_value
    return parsed


def _parse_orchestration_table(path: Path, table: object) -> dict[str, OrchestrationValue]:
    if not isinstance(table, dict):
        raise ValueError(f"missing [orchestration] in {path}")

    parsed: dict[str, OrchestrationValue] = {}
    for key, value in table.items():
        if not isinstance(key, str):
            raise ValueError(f"invalid orchestration key in {path}: {key!r}")
        if isinstance(value, str):
            parsed[key] = value
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            parsed[key] = list(value)
            continue
        raise ValueError(
            f"invalid orchestration value for {key} in {path}: expected str or list[str]"
        )
    return parsed


def _load_workflow_policy() -> TomlDict:
    return _load_toml(WORKFLOW_POLICY_PATH)


WORKFLOW_POLICY = _load_workflow_policy()

PUBLIC_SURFACE_POLICY = _require_table(WORKFLOW_POLICY, "public_surface", path=WORKFLOW_POLICY_PATH)
PROJECTION_POLICY = _require_table(WORKFLOW_POLICY, "projection", path=WORKFLOW_POLICY_PATH)
CODEX_POLICY = _require_table(WORKFLOW_POLICY, "codex", path=WORKFLOW_POLICY_PATH)
HELPER_CLOSE_POLICY = _require_table(WORKFLOW_POLICY, "helper_close", path=WORKFLOW_POLICY_PATH)
TASK_DOCUMENTS_POLICY = _require_table(WORKFLOW_POLICY, "task_documents", path=WORKFLOW_POLICY_PATH)

LONG_RUNNING_PUBLIC_SURFACE = _require_str_list(
    PUBLIC_SURFACE_POLICY, "long_running", path=WORKFLOW_POLICY_PATH
)
REQUIRED_HELPER_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY, "required_helper_agent_ids", path=WORKFLOW_POLICY_PATH
)
WRITABLE_PROJECTION_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY, "writable_projection_agent_ids", path=WORKFLOW_POLICY_PATH
)
DISABLED_WRITABLE_PROJECTION_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY,
    "disabled_writable_projection_agent_ids",
    path=WORKFLOW_POLICY_PATH,
)
DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY, "documentation_only_builtins", path=WORKFLOW_POLICY_PATH
)
INTERNAL_PLANNING_ROLE_IDS = _require_str_list(
    PROJECTION_POLICY, "internal_planning_role_ids", path=WORKFLOW_POLICY_PATH
)

EXPECTED_CODEX_REASONING_EFFORT = _require_str(
    CODEX_POLICY, "expected_reasoning_effort", path=WORKFLOW_POLICY_PATH
)
EXPECTED_CODEX_SANDBOX_BY_AGENT = _require_str_map(
    CODEX_POLICY, "sandbox_overrides", path=WORKFLOW_POLICY_PATH
)

STRONG_CLOSE_REASONS = list(
    _require_str_list(HELPER_CLOSE_POLICY, "strong_close_reasons", path=WORKFLOW_POLICY_PATH)
)
ADVISORY_TIMEOUT_POLICY = _require_str(
    HELPER_CLOSE_POLICY, "advisory_timeout_policy", path=WORKFLOW_POLICY_PATH
)
NON_ADVISORY_TIMEOUT_POLICY = _require_str(
    HELPER_CLOSE_POLICY, "non_advisory_timeout_policy", path=WORKFLOW_POLICY_PATH
)
INVALID_CLOSE_REASON = _require_str(
    HELPER_CLOSE_POLICY, "invalid_close_reason", path=WORKFLOW_POLICY_PATH
)
HELPER_CLOSE_ACK_DEFINITION = _require_str(
    HELPER_CLOSE_POLICY, "helper_close_ack_definition", path=WORKFLOW_POLICY_PATH
)
TERMINAL_RUNTIME_STATUSES = _require_str_list(
    HELPER_CLOSE_POLICY, "terminal_runtime_statuses", path=WORKFLOW_POLICY_PATH
)

PLAN_SECTION_ORDER = _require_str_list(
    TASK_DOCUMENTS_POLICY, "plan_section_order", path=WORKFLOW_POLICY_PATH
)
STATUS_SECTION_ORDER = _require_str_list(
    TASK_DOCUMENTS_POLICY, "status_section_order", path=WORKFLOW_POLICY_PATH
)
LEGACY_MILESTONE_SKILL_NAMES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "legacy_milestone_skill_names", path=WORKFLOW_POLICY_PATH
)
GENERATED_SKILL_MANIFEST_NAME = _require_str(
    TASK_DOCUMENTS_POLICY, "generated_skill_manifest_name", path=WORKFLOW_POLICY_PATH
)


def _load_agent_contract(agent_id: str) -> TomlDict:
    path = AGENT_REGISTRY_ROOT / agent_id / "agent.toml"
    if not path.exists():
        raise ValueError(f"missing agent contract: {path}")
    return _load_toml(path)


AGENT_CONTRACTS_BY_ID: dict[str, TomlDict] = {}
for _agent_dir in sorted(AGENT_REGISTRY_ROOT.iterdir()):
    if not _agent_dir.is_dir():
        continue
    agent_path = _agent_dir / "agent.toml"
    if not agent_path.exists():
        continue
    _contract = _load_toml(agent_path)
    _agent_id = _contract.get("id")
    if not isinstance(_agent_id, str) or not _agent_id.strip():
        raise ValueError(f"missing id in {agent_path}")
    AGENT_CONTRACTS_BY_ID[_agent_id] = _contract


def _expected_helper_orchestration() -> dict[str, dict[str, OrchestrationValue]]:
    expected: dict[str, dict[str, OrchestrationValue]] = {}
    for agent_id in REQUIRED_HELPER_AGENT_IDS:
        contract = AGENT_CONTRACTS_BY_ID.get(agent_id)
        if contract is None:
            raise ValueError(f"missing required helper registry entry: {agent_id}")
        path = AGENT_REGISTRY_ROOT / agent_id / "agent.toml"
        expected[agent_id] = _parse_orchestration_table(path, contract.get("orchestration"))
    return expected


CORE_HELPER_ORCHESTRATION_EXPECTED = _expected_helper_orchestration()

ADVISORY_HELPER_AGENT_IDS = tuple(
    agent_id
    for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items()
    if expected.get("blocking_class") == "advisory"
)


@dataclass(frozen=True)
class HelperCloseSnapshot:
    helper_id: str
    blocking_class: str
    result_contract: str
    close_protocol: str
    late_result_policy: str
    timeout_policy: str
    allowed_close_reasons: tuple[str, ...] = tuple(STRONG_CLOSE_REASONS)
    runtime_status: str = "running"
    observed: bool = False
    status_pinged: bool = False
    interrupt_sent: bool = False
    drain_grace_elapsed: bool = False
    wait_timed_out_count: int = 0
    close_reason: str | None = None
    has_preliminary: bool = False
    has_checkpoint: bool = False
    has_final: bool = False
    has_terminal_runtime_ack: bool = False

    def has_result(self) -> bool:
        return self.has_preliminary or self.has_checkpoint or self.has_final

    def has_ack(self) -> bool:
        return (
            self.has_result()
            or self.has_terminal_runtime_ack
            or self.runtime_status in TERMINAL_RUNTIME_STATUSES
        )


@dataclass(frozen=True)
class HelperCloseDecision:
    action: str
    close_allowed: bool
    accept_late_result: bool
    rationale: str


@dataclass(frozen=True)
class AdvisorySliceContext:
    helper_id: str
    files_changed: int = 0
    tests_changed: bool = False
    risky_logic_changed: bool = False
    explicit_review_requested: bool = False
    public_surface_changed: bool = False
    module_boundaries_changed: int = 0
    shared_types_changed: bool = False
    generics_changed: bool = False
    public_contract_changed: bool = False
    regression_risk_notable: bool = False
    coverage_gap: bool = False
    diff_is_nontrivial: bool = False
    is_frontend_slice: bool = False
    needs_discovery: bool = False
    can_change_current_decision: bool = True


def _accept_late_result(late_result_policy: str) -> bool:
    return late_result_policy == "merge-if-relevant"


def _decision(
    action: str,
    snapshot: HelperCloseSnapshot,
    close_allowed: bool,
    rationale: str,
) -> HelperCloseDecision:
    return HelperCloseDecision(
        action=action,
        close_allowed=close_allowed,
        accept_late_result=_accept_late_result(snapshot.late_result_policy),
        rationale=rationale,
    )


def _has_protocol_completion(snapshot: HelperCloseSnapshot) -> bool:
    return snapshot.has_ack() and snapshot.interrupt_sent and snapshot.drain_grace_elapsed


def decide_helper_close_action(snapshot: HelperCloseSnapshot) -> HelperCloseDecision:
    strong_close_reasons = set(snapshot.allowed_close_reasons)
    close_reason = snapshot.close_reason
    has_strong_reason = close_reason in strong_close_reasons

    if close_reason == INVALID_CLOSE_REASON:
        action = "background" if snapshot.blocking_class == "advisory" else "observe"
        return _decision(
            action,
            snapshot,
            close_allowed=False,
            rationale=f"`{INVALID_CLOSE_REASON}` is not a valid close reason",
        )

    if not snapshot.observed:
        return _decision("observe", snapshot, False, "close preflight starts with observe")

    if (
        snapshot.blocking_class == "advisory"
        and snapshot.runtime_status == "running"
        and snapshot.wait_timed_out_count > 0
        and not has_strong_reason
        and not snapshot.has_result()
    ):
        if not snapshot.status_pinged:
            return _decision(
                "status-ping",
                snapshot,
                False,
                "timed-out advisory helper must be status-pinged before any close decision",
            )
        return _decision(
            "background",
            snapshot,
            False,
            "advisory nonresponse stays background/advisory until strong close reason or ack",
        )

    if snapshot.runtime_status == "running" and not snapshot.status_pinged:
        return _decision(
            "status-ping",
            snapshot,
            False,
            "running helper requires status ping before interrupt/close",
        )

    if (has_strong_reason or snapshot.has_ack()) and (
        not snapshot.interrupt_sent or not snapshot.drain_grace_elapsed
    ):
        return _decision(
            "interrupt-and-drain",
            snapshot,
            False,
            "close requires interrupt flush and drain grace before close judgment",
        )

    if has_strong_reason and not snapshot.has_ack():
        action = "background" if snapshot.blocking_class == "advisory" else "observe"
        return _decision(
            action,
            snapshot,
            False,
            f"strong close reason requires protocol completion ack ({HELPER_CLOSE_ACK_DEFINITION})",
        )

    if has_strong_reason and _has_protocol_completion(snapshot):
        return _decision(
            "allow-close",
            snapshot,
            True,
            f"strong close reason and ack satisfied ({HELPER_CLOSE_ACK_DEFINITION}): {close_reason}",
        )

    if snapshot.blocking_class == "advisory" and snapshot.timeout_policy == ADVISORY_TIMEOUT_POLICY:
        return _decision(
            "background",
            snapshot,
            False,
            "advisory helper remains background until strong close reason or ack",
        )

    return _decision("observe", snapshot, False, "continue observing helper state")


def should_spawn_advisory_helper(slice_context: AdvisorySliceContext) -> bool:
    helper_id = slice_context.helper_id
    if helper_id not in ADVISORY_HELPER_AGENT_IDS:
        return False
    if not slice_context.can_change_current_decision:
        return False

    if helper_id == "explorer":
        return slice_context.needs_discovery
    if helper_id == "architecture-reviewer":
        return (
            slice_context.files_changed >= 7
            or slice_context.module_boundaries_changed >= 2
            or slice_context.public_surface_changed
        )
    if helper_id == "code-quality-reviewer":
        return (
            slice_context.files_changed >= 3
            or slice_context.tests_changed
            or slice_context.risky_logic_changed
            or slice_context.explicit_review_requested
        )
    if helper_id == "type-specialist":
        return (
            slice_context.shared_types_changed
            or slice_context.generics_changed
            or slice_context.public_contract_changed
        )
    if helper_id == "test-engineer":
        return slice_context.regression_risk_notable or slice_context.coverage_gap
    if helper_id == "module-structure-gatekeeper":
        return slice_context.diff_is_nontrivial
    if helper_id == "frontend-structure-gatekeeper":
        return slice_context.diff_is_nontrivial and slice_context.is_frontend_slice

    return False


def extract_level1_headings(markdown: str) -> list[str]:
    headings: list[str] = []
    for line in markdown.splitlines():
        if not line.startswith("# "):
            continue
        heading = line[2:].strip()
        if heading:
            headings.append(heading)
    return headings


def validate_section_order(markdown: str, expected_sections: tuple[str, ...]) -> str | None:
    headings = extract_level1_headings(markdown)
    cursor = 0
    for section in expected_sections:
        try:
            index = headings.index(section, cursor)
        except ValueError:
            return f"missing or out-of-order section: {section}"
        cursor = index + 1
    return None


def validate_markdown_sections(path: Path, expected_sections: tuple[str, ...]) -> str | None:
    content = path.read_text(encoding="utf-8")
    error = validate_section_order(content, expected_sections)
    if error is None:
        return None
    return f"{path}: {error}"
