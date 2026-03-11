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


def _require_str_list_map(table: TomlDict, key: str, *, path: Path) -> dict[str, tuple[str, ...]]:
    value = table.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing table [{key}] in {path}")

    parsed: dict[str, tuple[str, ...]] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str):
            raise ValueError(f"invalid key in '{key}' for {path}")
        if not isinstance(item_value, list) or not all(isinstance(item, str) and item.strip() for item in item_value):
            raise ValueError(f"invalid string list map '{key}.{item_key}' in {path}")
        parsed[item_key] = tuple(item_value)
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
TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_execution_plan_section_order", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_CORE_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_core_docs", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_task_yaml_required_keys", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_WORK_TYPES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_work_types", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_IMPACT_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_impact_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_VALIDATION_GATES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_validation_gate_values", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_BLOCKING_VALIDATION_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_blocking_validation_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_DESIGN_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_design_docs", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_UX_SPEC_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_ux_spec_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_TECH_SPEC_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_tech_spec_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_PUBLIC_CONTRACT_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_public_contract_docs", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_DATA_CONTRACT_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_data_contract_docs", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_BUGFIX_REGRESSION_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_bugfix_regression_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_REFACTOR_ACCEPTANCE_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_refactor_acceptance_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_PROTOTYPE_ACCEPTANCE_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_prototype_acceptance_flags", path=WORKFLOW_POLICY_PATH
)
SPEC_VALIDATION_SECTION_ORDER = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_spec_validation_section_order", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_TRACEABILITY_IDS = _require_str_map(
    TASK_DOCUMENTS_POLICY, "bundle_traceability_ids", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_BASE_DOCS = _require_str_list_map(
    TASK_DOCUMENTS_POLICY, "bundle_base_docs", path=WORKFLOW_POLICY_PATH
)
LEGACY_MILESTONE_SKILL_NAMES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "legacy_milestone_skill_names", path=WORKFLOW_POLICY_PATH
)
GENERATED_SKILL_MANIFEST_NAME = _require_str(
    TASK_DOCUMENTS_POLICY, "generated_skill_manifest_name", path=WORKFLOW_POLICY_PATH
)

TASK_BUNDLE_CORE_REQUIRED_DOCS = tuple(doc_name for doc_name in TASK_BUNDLE_CORE_DOCS if doc_name != "task.yaml")


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


@dataclass(frozen=True)
class TaskBundleManifest:
    task: str
    goal: str
    success_criteria: tuple[str, ...]
    major_boundaries: tuple[str, ...]
    work_type: str
    impact_flags: tuple[str, ...]
    required_docs: tuple[str, ...]
    source_of_truth: dict[str, str]
    ids: dict[str, str]
    validation_gate: str
    current_phase: str


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


def _next_meaningful_line(lines: list[str], index: int) -> int:
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped and not stripped.startswith("#"):
            return index
        index += 1
    return index


def _leading_spaces(value: str) -> int:
    return len(value) - len(value.lstrip(" "))


def _parse_yaml_scalar(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _parse_simple_yaml_list(lines: list[str], index: int, indent: int) -> tuple[list[str], int]:
    items: list[str] = []
    cursor = index
    while True:
        cursor = _next_meaningful_line(lines, cursor)
        if cursor >= len(lines):
            return items, cursor

        line = lines[cursor]
        current_indent = _leading_spaces(line)
        stripped = line.strip()
        if current_indent < indent:
            return items, cursor
        if current_indent != indent or not stripped.startswith("- "):
            raise ValueError(f"invalid YAML list item: {line!r}")

        item = stripped[2:].strip()
        if not item:
            raise ValueError("nested YAML lists are not supported")
        items.append(_parse_yaml_scalar(item))
        cursor += 1


def _parse_simple_yaml_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, object], int]:
    mapping: dict[str, object] = {}
    cursor = index
    while True:
        cursor = _next_meaningful_line(lines, cursor)
        if cursor >= len(lines):
            return mapping, cursor

        line = lines[cursor]
        current_indent = _leading_spaces(line)
        stripped = line.strip()
        if current_indent < indent:
            return mapping, cursor
        if current_indent != indent:
            raise ValueError(f"unexpected YAML indentation at line: {line!r}")
        if stripped.startswith("- "):
            raise ValueError(f"unexpected YAML list item in mapping: {line!r}")
        if ":" not in stripped:
            raise ValueError(f"invalid YAML mapping line: {line!r}")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise ValueError(f"invalid YAML key in line: {line!r}")

        if value:
            mapping[key] = _parse_yaml_scalar(value)
            cursor += 1
            continue

        next_cursor = _next_meaningful_line(lines, cursor + 1)
        if next_cursor >= len(lines):
            mapping[key] = {}
            return mapping, next_cursor

        next_line = lines[next_cursor]
        next_indent = _leading_spaces(next_line)
        if next_indent <= indent:
            mapping[key] = {}
            cursor = next_cursor
            continue
        if next_indent != indent + 2:
            raise ValueError(f"unsupported YAML indentation under {key!r}: {next_line!r}")

        if next_line.strip().startswith("- "):
            child, cursor = _parse_simple_yaml_list(lines, next_cursor, next_indent)
        else:
            child, cursor = _parse_simple_yaml_mapping(lines, next_cursor, next_indent)
        mapping[key] = child


def load_task_bundle_manifest(path: Path) -> TaskBundleManifest:
    lines = path.read_text(encoding="utf-8").splitlines()
    parsed, cursor = _parse_simple_yaml_mapping(lines, 0, 0)
    cursor = _next_meaningful_line(lines, cursor)
    if cursor < len(lines):
        raise ValueError(f"unexpected trailing YAML content in {path}: {lines[cursor]!r}")

    missing_keys = [key for key in TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS if key not in parsed]
    if missing_keys:
        raise ValueError(f"{path}: missing task.yaml keys: {missing_keys}")

    task = parsed["task"]
    goal = parsed["goal"]
    success_criteria = parsed["success_criteria"]
    major_boundaries = parsed["major_boundaries"]
    work_type = parsed["work_type"]
    impact_flags = parsed["impact_flags"]
    required_docs = parsed["required_docs"]
    source_of_truth = parsed["source_of_truth"]
    ids = parsed["ids"]
    validation_gate = parsed["validation_gate"]
    current_phase = parsed["current_phase"]

    if not all(isinstance(value, str) and value.strip() for value in (task, goal, work_type, validation_gate, current_phase)):
        raise ValueError(f"{path}: task, goal, work_type, validation_gate, current_phase must be non-empty strings")
    if not isinstance(success_criteria, list) or not all(
        isinstance(item, str) and item.strip() for item in success_criteria
    ):
        raise ValueError(f"{path}: success_criteria must be a list of strings")
    if not isinstance(major_boundaries, list) or not all(
        isinstance(item, str) and item.strip() for item in major_boundaries
    ):
        raise ValueError(f"{path}: major_boundaries must be a list of strings")
    if not isinstance(impact_flags, list) or not all(isinstance(item, str) and item.strip() for item in impact_flags):
        raise ValueError(f"{path}: impact_flags must be a list of strings")
    if not isinstance(required_docs, list) or not all(isinstance(item, str) and item.strip() for item in required_docs):
        raise ValueError(f"{path}: required_docs must be a list of strings")
    if not isinstance(source_of_truth, dict) or not all(
        isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip()
        for key, value in source_of_truth.items()
    ):
        raise ValueError(f"{path}: source_of_truth must be a string map")
    if not isinstance(ids, dict) or not all(
        isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip()
        for key, value in ids.items()
    ):
        raise ValueError(f"{path}: ids must be a string map")

    return TaskBundleManifest(
        task=task,
        goal=goal,
        success_criteria=tuple(success_criteria),
        major_boundaries=tuple(major_boundaries),
        work_type=work_type,
        impact_flags=tuple(impact_flags),
        required_docs=tuple(required_docs),
        source_of_truth={key: value for key, value in source_of_truth.items()},
        ids={key: value for key, value in ids.items()},
        validation_gate=validation_gate,
        current_phase=current_phase,
    )


def derive_task_bundle_required_docs(work_type: str, impact_flags: tuple[str, ...]) -> tuple[str, ...]:
    if work_type not in TASK_BUNDLE_WORK_TYPES:
        raise ValueError(f"unsupported work_type: {work_type}")
    if any(flag not in TASK_BUNDLE_IMPACT_FLAGS for flag in impact_flags):
        unknown_flags = sorted(flag for flag in impact_flags if flag not in TASK_BUNDLE_IMPACT_FLAGS)
        raise ValueError(f"unsupported impact_flags: {unknown_flags}")

    docs = set(TASK_BUNDLE_CORE_REQUIRED_DOCS)
    docs.update(TASK_BUNDLE_BASE_DOCS[work_type])

    if set(impact_flags) & set(TASK_BUNDLE_UX_SPEC_FLAGS):
        docs.add("UX_SPEC.md")
    if set(impact_flags) & set(TASK_BUNDLE_TECH_SPEC_FLAGS):
        docs.add("TECH_SPEC.md")
    if "public_contract_changed" in impact_flags:
        docs.update(TASK_BUNDLE_PUBLIC_CONTRACT_DOCS)
    if "data_contract_changed" in impact_flags:
        docs.update(TASK_BUNDLE_DATA_CONTRACT_DOCS)
    if "architecture_significant" in impact_flags:
        docs.add("ADRs/")
    if work_type == "bugfix" and set(impact_flags) & set(TASK_BUNDLE_BUGFIX_REGRESSION_FLAGS):
        docs.add("REGRESSION.md")
    if work_type == "refactor" and set(impact_flags) & set(TASK_BUNDLE_REFACTOR_ACCEPTANCE_FLAGS):
        docs.add("ACCEPTANCE.feature")
    if work_type == "prototype" and set(impact_flags) & set(TASK_BUNDLE_PROTOTYPE_ACCEPTANCE_FLAGS):
        docs.add("ACCEPTANCE.feature")

    return tuple(sorted(docs))


def decide_spec_validation_gate(impact_flags: tuple[str, ...], required_docs: tuple[str, ...]) -> str:
    if any(flag in TASK_BUNDLE_BLOCKING_VALIDATION_FLAGS for flag in impact_flags):
        return "blocking"

    design_doc_count = 0
    for document in required_docs:
        if document in TASK_BUNDLE_DESIGN_DOCS or document == "ADRs/":
            design_doc_count += 1
    return "blocking" if design_doc_count >= 3 else "advisory"


def _validate_required_doc_paths(task_root: Path, required_docs: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for document in required_docs:
        path = task_root / document
        if document.endswith("/"):
            if not path.exists() or not path.is_dir():
                errors.append(f"{task_root}: missing required directory: {document}")
                continue
            if document == "ADRs/" and not list(path.glob("ADR-*.md")):
                errors.append(f"{task_root}: ADRs/ must contain at least one ADR-*.md")
            continue
        if not path.exists() or not path.is_file():
            errors.append(f"{task_root}: missing required document: {document}")
    return errors


def validate_task_bundle_root(task_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = task_root / "task.yaml"
    if not manifest_path.exists():
        return [f"{task_root}: missing task.yaml"]
    if (task_root / "PLAN.md").exists():
        errors.append(f"{task_root}: mixed task mode is not allowed (`task.yaml` and `PLAN.md`)")

    try:
        manifest = load_task_bundle_manifest(manifest_path)
    except ValueError as exc:
        return [str(exc)]

    for core_doc in TASK_BUNDLE_CORE_DOCS:
        path = task_root / core_doc
        exists = path.is_dir() if core_doc.endswith("/") else path.is_file()
        if not exists:
            errors.append(f"{task_root}: missing core document: {core_doc}")

    if manifest.work_type not in TASK_BUNDLE_WORK_TYPES:
        errors.append(f"{task_root}: unsupported work_type: {manifest.work_type}")
    if any(flag not in TASK_BUNDLE_IMPACT_FLAGS for flag in manifest.impact_flags):
        unknown_flags = sorted(flag for flag in manifest.impact_flags if flag not in TASK_BUNDLE_IMPACT_FLAGS)
        errors.append(f"{task_root}: unsupported impact_flags: {unknown_flags}")
    if manifest.validation_gate not in TASK_BUNDLE_VALIDATION_GATES:
        errors.append(f"{task_root}: unsupported validation_gate: {manifest.validation_gate}")
    if manifest.ids != TASK_BUNDLE_TRACEABILITY_IDS:
        errors.append(f"{task_root}: ids must match fixed traceability prefixes")
    if not manifest.success_criteria:
        errors.append(f"{task_root}: success_criteria must not be empty")
    if not manifest.major_boundaries:
        errors.append(f"{task_root}: major_boundaries must not be empty")

    missing_core_from_manifest = sorted(set(TASK_BUNDLE_CORE_REQUIRED_DOCS) - set(manifest.required_docs))
    if missing_core_from_manifest:
        errors.append(f"{task_root}: required_docs missing core docs: {missing_core_from_manifest}")
    if "task.yaml" in manifest.required_docs:
        errors.append(f"{task_root}: required_docs must not include task.yaml")

    errors.extend(_validate_required_doc_paths(task_root, manifest.required_docs))

    expected_docs = set(derive_task_bundle_required_docs(manifest.work_type, manifest.impact_flags))
    missing_expected_docs = sorted(expected_docs - set(manifest.required_docs))
    if missing_expected_docs:
        errors.append(f"{task_root}: required_docs missing derived docs: {missing_expected_docs}")

    expected_gate = decide_spec_validation_gate(manifest.impact_flags, manifest.required_docs)
    if manifest.validation_gate != expected_gate:
        errors.append(
            f"{task_root}: validation_gate mismatch: expected={expected_gate!r} actual={manifest.validation_gate!r}"
        )

    if manifest.source_of_truth.get("execution") != "EXECUTION_PLAN.md":
        errors.append(f"{task_root}: source_of_truth.execution must point to EXECUTION_PLAN.md")
    if manifest.source_of_truth.get("validation") != "SPEC_VALIDATION.md":
        errors.append(f"{task_root}: source_of_truth.validation must point to SPEC_VALIDATION.md")

    optional_sources = {
        "product": "PRD.md",
        "ux": "UX_SPEC.md",
        "architecture": "TECH_SPEC.md",
        "acceptance": "ACCEPTANCE.feature",
    }
    for source_key, source_path in optional_sources.items():
        if source_path in manifest.required_docs and manifest.source_of_truth.get(source_key) != source_path:
            errors.append(f"{task_root}: source_of_truth.{source_key} must point to {source_path}")

    for source_key, relative_path in manifest.source_of_truth.items():
        source_path = task_root / relative_path
        if not source_path.exists():
            errors.append(f"{task_root}: source_of_truth.{source_key} points to missing file: {relative_path}")

    spec_error = validate_markdown_sections(task_root / "SPEC_VALIDATION.md", SPEC_VALIDATION_SECTION_ORDER)
    if spec_error is not None:
        errors.append(spec_error)
    execution_plan_error = validate_markdown_sections(
        task_root / "EXECUTION_PLAN.md",
        TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    )
    if execution_plan_error is not None:
        errors.append(execution_plan_error)
    status_error = validate_markdown_sections(task_root / "STATUS.md", STATUS_SECTION_ORDER)
    if status_error is not None:
        errors.append(status_error)

    return errors


def detect_task_document_mode(task_root: Path) -> str | None:
    has_bundle = (task_root / "task.yaml").exists()
    has_legacy = (task_root / "PLAN.md").exists()
    has_status = (task_root / "STATUS.md").exists()

    if has_bundle and has_legacy:
        return "mixed"
    if has_bundle:
        return "bundle"
    if has_legacy:
        return "legacy"
    if has_status:
        return "invalid"
    return None


def validate_legacy_task_root(task_root: Path) -> list[str]:
    errors: list[str] = []
    plan_path = task_root / "PLAN.md"
    status_path = task_root / "STATUS.md"

    if not plan_path.exists():
        errors.append(f"{task_root}: missing PLAN.md")
        return errors

    plan_error = validate_markdown_sections(plan_path, PLAN_SECTION_ORDER)
    if plan_error is not None:
        errors.append(plan_error)

    if not status_path.exists():
        errors.append(f"{task_root}: legacy task must include STATUS.md")
        return errors

    status_error = validate_markdown_sections(status_path, STATUS_SECTION_ORDER)
    if status_error is not None:
        errors.append(status_error)

    return errors
