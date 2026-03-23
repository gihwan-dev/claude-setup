#!/usr/bin/env python3
from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, replace
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import TypeAlias

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_ROOT = REPO_ROOT / "policy"
WORKFLOW_POLICY_PATH = POLICY_ROOT / "workflow.toml"
AGENT_REGISTRY_ROOT = REPO_ROOT / "agent-registry"

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


def _require_int(table: TomlDict, key: str, *, path: Path) -> int:
    value = table.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"missing integer '{key}' in {path}")
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


def _optional_str_list(table: TomlDict, key: str, *, path: Path) -> tuple[str, ...]:
    value = table.get(key)
    if value is None:
        return tuple()
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"invalid optional string list '{key}' in {path}")
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


def _require_limit_map(table: TomlDict, key: str, *, path: Path) -> dict[str, dict[str, int]]:
    value = table.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing table [{key}] in {path}")

    parsed: dict[str, dict[str, int]] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, dict):
            raise ValueError(f"invalid limit map '{key}' in {path}")

        target = item_value.get("target")
        hard = item_value.get("hard")
        if (
            isinstance(target, bool)
            or not isinstance(target, int)
            or isinstance(hard, bool)
            or not isinstance(hard, int)
            or target <= 0
            or hard <= 0
            or target > hard
        ):
            raise ValueError(f"invalid limit pair '{key}.{item_key}' in {path}")
        parsed[item_key] = {"target": target, "hard": hard}
    return parsed




def _load_workflow_policy() -> TomlDict:
    return _load_toml(WORKFLOW_POLICY_PATH)


WORKFLOW_POLICY = _load_workflow_policy()

PUBLIC_SURFACE_POLICY = _require_table(WORKFLOW_POLICY, "public_surface", path=WORKFLOW_POLICY_PATH)
PROJECTION_POLICY = _require_table(WORKFLOW_POLICY, "projection", path=WORKFLOW_POLICY_PATH)
CODEX_POLICY = _require_table(WORKFLOW_POLICY, "codex", path=WORKFLOW_POLICY_PATH)
SLICE_BUDGET_POLICY = _require_table(WORKFLOW_POLICY, "slice_budget", path=WORKFLOW_POLICY_PATH)
STRUCTURE_REVIEW_POLICY = _require_table(
    WORKFLOW_POLICY, "structure_review", path=WORKFLOW_POLICY_PATH
)
TASK_DOCUMENTS_POLICY = _require_table(WORKFLOW_POLICY, "task_documents", path=WORKFLOW_POLICY_PATH)

LONG_RUNNING_PUBLIC_SURFACE = _require_str_list(
    PUBLIC_SURFACE_POLICY, "long_running", path=WORKFLOW_POLICY_PATH
)
REQUIRED_HELPER_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY, "required_helper_agent_ids", path=WORKFLOW_POLICY_PATH
)
DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS = _require_str_list(
    PROJECTION_POLICY, "documentation_only_builtins", path=WORKFLOW_POLICY_PATH
)
DEFAULT_CODEX_REASONING_EFFORT = _require_str(
    CODEX_POLICY, "default_reasoning_effort", path=WORKFLOW_POLICY_PATH
)
CODEX_REASONING_EFFORT_OVERRIDES = _optional_str_map(
    CODEX_POLICY, "reasoning_effort_overrides", path=WORKFLOW_POLICY_PATH
)
# Deprecated alias — kept for backward compatibility.
EXPECTED_CODEX_REASONING_EFFORT = DEFAULT_CODEX_REASONING_EFFORT

EXPECTED_CODEX_SANDBOX_BY_AGENT = _optional_str_map(
    CODEX_POLICY, "sandbox_overrides", path=WORKFLOW_POLICY_PATH
)


def expected_reasoning_effort_for(agent_id: str) -> str:
    return CODEX_REASONING_EFFORT_OVERRIDES.get(agent_id, DEFAULT_CODEX_REASONING_EFFORT)

SLICE_BUDGET_MAX_REPO_FILES = _require_int(
    SLICE_BUDGET_POLICY, "max_repo_files", path=WORKFLOW_POLICY_PATH
)
SLICE_BUDGET_MAX_NET_LOC = _require_int(
    SLICE_BUDGET_POLICY, "max_net_loc", path=WORKFLOW_POLICY_PATH
)
SLICE_BUDGET_ENFORCEMENT = _require_str(
    SLICE_BUDGET_POLICY, "enforcement", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_SOFT_LIMIT_BEHAVIOR = _require_str(
    STRUCTURE_REVIEW_POLICY, "soft_limit_behavior", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_HARD_LIMIT_BEHAVIOR = _require_str(
    STRUCTURE_REVIEW_POLICY, "hard_limit_behavior", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_RESPONSIBILITY_MIX_BEHAVIOR = _require_str(
    STRUCTURE_REVIEW_POLICY, "responsibility_mix_behavior", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_LEGACY_OVERSIZED_FILE_BEHAVIOR = _require_str(
    STRUCTURE_REVIEW_POLICY,
    "legacy_oversized_file_behavior",
    path=WORKFLOW_POLICY_PATH,
)
STRUCTURE_REVIEW_EXCEPTIONS = _require_str_list(
    STRUCTURE_REVIEW_POLICY, "exceptions", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_SPLIT_ROLES = _require_str_list(
    STRUCTURE_REVIEW_POLICY, "split_roles", path=WORKFLOW_POLICY_PATH
)
STRUCTURE_REVIEW_ROLE_LIMITS = _require_limit_map(
    STRUCTURE_REVIEW_POLICY, "role_limits", path=WORKFLOW_POLICY_PATH
)

if SLICE_BUDGET_MAX_REPO_FILES <= 0 or SLICE_BUDGET_MAX_NET_LOC <= 0:
    raise ValueError("slice_budget thresholds must be positive integers")
if SLICE_BUDGET_ENFORCEMENT != "split-before-execution":
    raise ValueError(
        f"slice_budget.enforcement must be 'split-before-execution', got {SLICE_BUDGET_ENFORCEMENT!r}"
    )
if STRUCTURE_REVIEW_SOFT_LIMIT_BEHAVIOR != "split-first":
    raise ValueError(
        "structure_review.soft_limit_behavior must be 'split-first'"
    )
if STRUCTURE_REVIEW_HARD_LIMIT_BEHAVIOR != "block":
    raise ValueError("structure_review.hard_limit_behavior must be 'block'")
if STRUCTURE_REVIEW_RESPONSIBILITY_MIX_BEHAVIOR != "block":
    raise ValueError(
        "structure_review.responsibility_mix_behavior must be 'block'"
    )

BROAD_SLICE_WORK_LABELS = frozenset({"setup", "skeleton", "fsd-skeleton", "wrapper", "docs"})

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
TASK_BUNDLE_DELIVERY_STRATEGIES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_delivery_strategies", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_EXECUTION_TOPOLOGIES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_execution_topologies", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_CSV_FANOUT_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_csv_fanout_docs", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_csv_fanout_orchestration_required_keys", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_UI_FIRST_WORK_TYPES = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_ui_first_work_types", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_UI_FIRST_FLAGS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_ui_first_flags", path=WORKFLOW_POLICY_PATH
)
TASK_BUNDLE_UI_REQUIRED_DOCS = _require_str_list(
    TASK_DOCUMENTS_POLICY, "bundle_ui_required_docs", path=WORKFLOW_POLICY_PATH
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
TASK_BUNDLE_OPTIONAL_SOURCE_OF_TRUTH_PATHS = _require_str_map(
    TASK_DOCUMENTS_POLICY, "bundle_optional_source_of_truth_paths", path=WORKFLOW_POLICY_PATH
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


ADVISORY_HELPER_AGENT_IDS = tuple(
    agent_id for agent_id in REQUIRED_HELPER_AGENT_IDS
    if agent_id != "verification-worker"
)

DEFAULT_MULTI_WORK_EXPLORATION_HELPERS = ("explorer", "structure-reviewer")
BASELINE_MULTI_REVIEW_HELPERS = (
    "structure-reviewer",
    "code-quality-reviewer",
    "test-engineer",
)
OPTIONAL_MULTI_REVIEW_HELPERS = (
    "architecture-reviewer",
    "type-specialist",
    "react-state-reviewer",
    "browser-explorer",
)

MULTI_REVIEW_DIFF_ONLY = "diff-only"
MULTI_REVIEW_DIFF_AND_HOTSPOTS = "diff+full-file-hotspots"
MULTI_REVIEW_MAINTAINABILITY_CLEAR = "clear"
MULTI_REVIEW_MAINTAINABILITY_NOTE = "note"
MULTI_REVIEW_MAINTAINABILITY_SPLIT_FIRST = "split-first"
MULTI_REVIEW_MAINTAINABILITY_BLOCK_ADDITIVE_GROWTH = "block-additive-growth"
MULTI_REVIEW_FINDING_TYPES = (
    "correctness",
    "state",
    "test gap",
    "maintainability",
)
MAX_FULL_FILE_STRUCTURE_HOTSPOTS = 3
STRUCTURE_REVIEW_LIMIT_EXCEPTION = "exception"
STRUCTURE_REVIEW_LIMIT_WITHIN_LIMITS = "within-limits"
STRUCTURE_REVIEW_LIMIT_SOFT_OVERSIZED = "soft-oversized"
STRUCTURE_REVIEW_LIMIT_HARD_OVERSIZED = "hard-oversized"
STRUCTURE_REVIEW_LIMIT_LEGACY_ADDITIVE_GROWTH = "legacy-additive-growth"
STRUCTURE_REVIEW_LIMIT_LEGACY_NON_ADDITIVE = "legacy-oversized-non-additive"
STRUCTURE_REVIEW_LIMIT_RESPONSIBILITY_MIX = "responsibility-mix-risk"
STRUCTURE_REVIEW_ROLE_COMPONENT_VIEW = "component_view"
STRUCTURE_REVIEW_ROLE_REACT_HOOK = "react_hook_provider_view_model"
STRUCTURE_REVIEW_ROLE_SERVICE = "service_use_case_controller_repository_util_module"

_STRUCTURE_REVIEW_LIMIT_PRIORITY = {
    STRUCTURE_REVIEW_LIMIT_EXCEPTION: -1,
    STRUCTURE_REVIEW_LIMIT_WITHIN_LIMITS: 0,
    STRUCTURE_REVIEW_LIMIT_LEGACY_NON_ADDITIVE: 1,
    STRUCTURE_REVIEW_LIMIT_SOFT_OVERSIZED: 2,
    STRUCTURE_REVIEW_LIMIT_HARD_OVERSIZED: 3,
    STRUCTURE_REVIEW_LIMIT_RESPONSIBILITY_MIX: 3,
    STRUCTURE_REVIEW_LIMIT_LEGACY_ADDITIVE_GROWTH: 4,
}


def _normalize_review_path(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def _dedupe_preserving_order(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


@dataclass(frozen=True)
class ReviewTargetFile:
    path: str
    pre_loc: int
    post_loc: int
    net_loc_delta: int | None = None
    responsibility_mix_risk: bool = False

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("ReviewTargetFile.path must be a non-empty string")
        if self.pre_loc < 0 or self.post_loc < 0:
            raise ValueError("ReviewTargetFile LOC values must be non-negative")
        if self.net_loc_delta is None:
            object.__setattr__(self, "net_loc_delta", self.post_loc - self.pre_loc)


@dataclass(frozen=True)
class ReviewHotspot:
    path: str
    role: str
    pre_loc: int
    post_loc: int
    net_loc_delta: int
    limit_state: str
    needs_full_file_structure_review: bool
    reason_codes: tuple[str, ...] = tuple()


@dataclass(frozen=True)
class MultiReviewScope:
    review_mode: str = MULTI_REVIEW_DIFF_ONLY
    hotspot_paths: tuple[str, ...] = tuple()
    hotspots: tuple[ReviewHotspot, ...] = tuple()
    maintainability_verdict: str = MULTI_REVIEW_MAINTAINABILITY_CLEAR
    maintainability_reason_codes: tuple[str, ...] = tuple()


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
    needs_repo_exploration: bool = False
    needs_external_research: bool = False
    needs_browser_repro: bool = False
    review_mode: str = MULTI_REVIEW_DIFF_ONLY
    hotspot_paths: tuple[str, ...] = tuple()
    maintainability_verdict: str = MULTI_REVIEW_MAINTAINABILITY_CLEAR
    maintainability_reason_codes: tuple[str, ...] = tuple()
    can_change_current_decision: bool = True


@dataclass(frozen=True)
class SliceExecutionPlan:
    repo_files_planned: int = 0
    net_loc_planned: int = 0
    work_labels: tuple[str, ...] = tuple()


@dataclass(frozen=True)
class SliceExecutionDecision:
    action: str
    execution_allowed: bool
    rationale: str


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
    delivery_strategy: str
    validation_gate: str
    current_phase: str
    execution_topology: str = "keep-local"
    orchestration: dict[str, object] | None = None


def infer_structure_review_role(path: str) -> str:
    normalized = _normalize_review_path(path)
    pure_path = PurePosixPath(normalized)
    lower_parts = {part.lower() for part in pure_path.parts}
    lower_name = pure_path.name.lower()
    lower_stem = pure_path.stem.lower()

    if pure_path.suffix.lower() in {".tsx", ".jsx"}:
        return STRUCTURE_REVIEW_ROLE_COMPONENT_VIEW
    if lower_parts & {"ui", "view", "views", "widget", "widgets", "screen", "screens", "page", "pages"}:
        return STRUCTURE_REVIEW_ROLE_COMPONENT_VIEW
    if lower_name.startswith("use") or lower_stem.startswith("use"):
        return STRUCTURE_REVIEW_ROLE_REACT_HOOK
    if lower_parts & {"hook", "hooks", "provider", "providers", "view-model", "view-models", "context", "contexts"}:
        return STRUCTURE_REVIEW_ROLE_REACT_HOOK
    if any(token in lower_stem for token in ("hook", "provider", "view-model", "viewmodel", "context")):
        return STRUCTURE_REVIEW_ROLE_REACT_HOOK
    return STRUCTURE_REVIEW_ROLE_SERVICE


def is_structure_review_exception(path: str) -> bool:
    normalized = _normalize_review_path(path).lower()
    file_name = PurePosixPath(normalized).name
    for exception in STRUCTURE_REVIEW_EXCEPTIONS:
        lowered = exception.lower()
        if any(token in lowered for token in "*?[]"):
            if fnmatch(normalized, lowered) or fnmatch(file_name, lowered):
                return True
            continue
        if lowered == "route manifest" and "route" in normalized and "manifest" in normalized:
            return True
        if lowered == "icon registry" and "icon" in normalized and "registry" in normalized:
            return True
        if lowered == "schema declaration files" and normalized.endswith(".d.ts") and "schema" in normalized:
            return True
        if lowered == "migration snapshot" and "migration" in normalized and "snapshot" in normalized:
            return True
        if lowered == "vendored third-party" and any(
            token in normalized for token in ("vendor/", "vendors/", "third_party/", "third-party/", "node_modules/")
        ):
            return True
    return False


def _primary_hotspot_reason(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        return STRUCTURE_REVIEW_LIMIT_WITHIN_LIMITS
    return max(
        reason_codes,
        key=lambda code: _STRUCTURE_REVIEW_LIMIT_PRIORITY.get(code, 0),
    )


def classify_review_hotspot(review_file: ReviewTargetFile) -> ReviewHotspot:
    normalized_path = _normalize_review_path(review_file.path)
    role = infer_structure_review_role(normalized_path)
    pre_loc = review_file.pre_loc
    post_loc = review_file.post_loc
    net_loc_delta = review_file.net_loc_delta if review_file.net_loc_delta is not None else post_loc - pre_loc

    if is_structure_review_exception(normalized_path):
        return ReviewHotspot(
            path=normalized_path,
            role=role,
            pre_loc=pre_loc,
            post_loc=post_loc,
            net_loc_delta=net_loc_delta,
            limit_state=STRUCTURE_REVIEW_LIMIT_EXCEPTION,
            needs_full_file_structure_review=False,
        )

    limits = STRUCTURE_REVIEW_ROLE_LIMITS.get(role, STRUCTURE_REVIEW_ROLE_LIMITS[STRUCTURE_REVIEW_ROLE_SERVICE])
    target_limit = limits["target"]
    hard_limit = limits["hard"]
    pre_oversized = pre_loc > target_limit
    post_oversized = post_loc > target_limit

    reason_codes: list[str] = []
    if pre_oversized and net_loc_delta > 0:
        reason_codes.append(STRUCTURE_REVIEW_LIMIT_LEGACY_ADDITIVE_GROWTH)
    elif pre_oversized and net_loc_delta <= 0 and post_oversized:
        reason_codes.append(STRUCTURE_REVIEW_LIMIT_LEGACY_NON_ADDITIVE)
    elif post_loc > hard_limit:
        reason_codes.append(STRUCTURE_REVIEW_LIMIT_HARD_OVERSIZED)
    elif post_oversized:
        reason_codes.append(STRUCTURE_REVIEW_LIMIT_SOFT_OVERSIZED)

    if review_file.responsibility_mix_risk:
        reason_codes.append(STRUCTURE_REVIEW_LIMIT_RESPONSIBILITY_MIX)

    ordered_reason_codes = _dedupe_preserving_order(reason_codes)
    limit_state = _primary_hotspot_reason(ordered_reason_codes)
    needs_full_file_structure_review = limit_state != STRUCTURE_REVIEW_LIMIT_WITHIN_LIMITS

    return ReviewHotspot(
        path=normalized_path,
        role=role,
        pre_loc=pre_loc,
        post_loc=post_loc,
        net_loc_delta=net_loc_delta,
        limit_state=limit_state,
        needs_full_file_structure_review=needs_full_file_structure_review,
        reason_codes=ordered_reason_codes,
    )


def _hotspot_sort_key(hotspot: ReviewHotspot) -> tuple[int, int, int, str]:
    return (
        -_STRUCTURE_REVIEW_LIMIT_PRIORITY.get(hotspot.limit_state, 0),
        -hotspot.post_loc,
        -(hotspot.net_loc_delta),
        hotspot.path,
    )


def _derive_maintainability_verdict(hotspots: tuple[ReviewHotspot, ...]) -> str:
    reason_codes = {
        reason_code
        for hotspot in hotspots
        for reason_code in hotspot.reason_codes
    }
    if STRUCTURE_REVIEW_LIMIT_LEGACY_ADDITIVE_GROWTH in reason_codes:
        return MULTI_REVIEW_MAINTAINABILITY_BLOCK_ADDITIVE_GROWTH
    if reason_codes & {
        STRUCTURE_REVIEW_LIMIT_SOFT_OVERSIZED,
        STRUCTURE_REVIEW_LIMIT_HARD_OVERSIZED,
        STRUCTURE_REVIEW_LIMIT_RESPONSIBILITY_MIX,
    }:
        return MULTI_REVIEW_MAINTAINABILITY_SPLIT_FIRST
    if STRUCTURE_REVIEW_LIMIT_LEGACY_NON_ADDITIVE in reason_codes:
        return MULTI_REVIEW_MAINTAINABILITY_NOTE
    return MULTI_REVIEW_MAINTAINABILITY_CLEAR


def derive_multi_review_scope(
    review_target_files: tuple[ReviewTargetFile, ...],
    *,
    max_full_file_hotspots: int = MAX_FULL_FILE_STRUCTURE_HOTSPOTS,
) -> MultiReviewScope:
    if max_full_file_hotspots <= 0:
        raise ValueError("max_full_file_hotspots must be positive")

    all_hotspots = tuple(
        classify_review_hotspot(review_target_file)
        for review_target_file in review_target_files
    )
    full_file_hotspots = tuple(
        sorted(
            (
                hotspot
                for hotspot in all_hotspots
                if hotspot.needs_full_file_structure_review
            ),
            key=_hotspot_sort_key,
        )
    )
    selected_hotspots = full_file_hotspots[:max_full_file_hotspots]

    reason_codes = [
        reason_code
        for hotspot in full_file_hotspots
        for reason_code in hotspot.reason_codes
    ]
    if len(full_file_hotspots) > max_full_file_hotspots:
        reason_codes.append("hotspot-cap-exceeded")

    if not selected_hotspots:
        return MultiReviewScope()

    return MultiReviewScope(
        review_mode=MULTI_REVIEW_DIFF_AND_HOTSPOTS,
        hotspot_paths=tuple(hotspot.path for hotspot in selected_hotspots),
        hotspots=selected_hotspots,
        maintainability_verdict=_derive_maintainability_verdict(full_file_hotspots),
        maintainability_reason_codes=_dedupe_preserving_order(reason_codes),
    )


def derive_multi_review_context(
    slice_context: AdvisorySliceContext,
    review_target_files: tuple[ReviewTargetFile, ...],
) -> AdvisorySliceContext:
    review_scope = derive_multi_review_scope(review_target_files)
    return replace(
        slice_context,
        review_mode=review_scope.review_mode,
        hotspot_paths=review_scope.hotspot_paths,
        maintainability_verdict=review_scope.maintainability_verdict,
        maintainability_reason_codes=review_scope.maintainability_reason_codes,
    )


def is_broad_execution_handoff(plan: SliceExecutionPlan) -> bool:
    broad_labels = {label for label in plan.work_labels if label in BROAD_SLICE_WORK_LABELS}
    return (
        plan.repo_files_planned > SLICE_BUDGET_MAX_REPO_FILES
        or plan.net_loc_planned > SLICE_BUDGET_MAX_NET_LOC
        or len(broad_labels) >= 2
    )


def decide_slice_execution_mode(plan: SliceExecutionPlan) -> SliceExecutionDecision:
    if is_broad_execution_handoff(plan):
        return SliceExecutionDecision(
            action="split-replan",
            execution_allowed=False,
            rationale=(
                f"broad PREP-0 style execution exceeds slice budget; "
                f"{SLICE_BUDGET_ENFORCEMENT} requires split/replan before execution "
                f"({SLICE_BUDGET_MAX_REPO_FILES} files / {SLICE_BUDGET_MAX_NET_LOC} net LOC)"
            ),
        )

    return SliceExecutionDecision(
        action="allow",
        execution_allowed=True,
        rationale="slice stays within budget; execute the slice and run to boundary",
    )


def derive_multi_work_helpers(
    *,
    needs_external_research: bool = False,
    needs_browser_repro: bool = False,
) -> tuple[str, ...]:
    helpers = list(DEFAULT_MULTI_WORK_EXPLORATION_HELPERS)
    if needs_external_research:
        helpers.append("web-researcher")
    if needs_browser_repro:
        helpers.append("browser-explorer")
    return tuple(helpers)


def should_spawn_advisory_helper(slice_context: AdvisorySliceContext) -> bool:
    helper_id = slice_context.helper_id
    if helper_id not in ADVISORY_HELPER_AGENT_IDS:
        return False
    if not slice_context.can_change_current_decision:
        return False

    if helper_id == "explorer":
        return slice_context.needs_repo_exploration
    if helper_id == "web-researcher":
        return slice_context.needs_external_research
    if helper_id == "browser-explorer":
        return slice_context.needs_browser_repro
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
    if helper_id == "structure-reviewer":
        return slice_context.diff_is_nontrivial or bool(slice_context.hotspot_paths)
    if helper_id == "react-state-reviewer":
        return slice_context.is_frontend_slice

    return False


def derive_multi_review_helpers(slice_context: AdvisorySliceContext) -> tuple[str, ...]:
    helpers = list(BASELINE_MULTI_REVIEW_HELPERS)
    for helper_id in OPTIONAL_MULTI_REVIEW_HELPERS:
        candidate = replace(slice_context, helper_id=helper_id)
        if should_spawn_advisory_helper(candidate):
            helpers.append(helper_id)
    return tuple(helpers)


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
    delivery_strategy = parsed["delivery_strategy"]
    validation_gate = parsed["validation_gate"]
    current_phase = parsed["current_phase"]

    execution_topology = parsed.get("execution_topology", "keep-local")
    if not isinstance(execution_topology, str) or not execution_topology.strip():
        execution_topology = "keep-local"
    orchestration = parsed.get("orchestration")
    if orchestration is not None and not isinstance(orchestration, dict):
        raise ValueError(f"{path}: orchestration must be a mapping")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (task, goal, work_type, delivery_strategy, validation_gate, current_phase)
    ):
        raise ValueError(
            f"{path}: task, goal, work_type, delivery_strategy, validation_gate, current_phase must be non-empty strings"
        )
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
        delivery_strategy=delivery_strategy,
        validation_gate=validation_gate,
        current_phase=current_phase,
        execution_topology=execution_topology,
        orchestration=orchestration if isinstance(orchestration, dict) else None,
    )


def derive_csv_fanout_docs(execution_topology: str) -> tuple[str, ...]:
    if execution_topology == "csv-fanout":
        return TASK_BUNDLE_CSV_FANOUT_DOCS
    if execution_topology == "hybrid":
        return tuple(TASK_BUNDLE_CSV_FANOUT_DOCS)
    return tuple()


def decide_task_bundle_delivery_strategy(work_type: str, impact_flags: tuple[str, ...]) -> str:
    if work_type not in TASK_BUNDLE_WORK_TYPES:
        raise ValueError(f"unsupported work_type: {work_type}")
    if any(flag not in TASK_BUNDLE_IMPACT_FLAGS for flag in impact_flags):
        unknown_flags = sorted(flag for flag in impact_flags if flag not in TASK_BUNDLE_IMPACT_FLAGS)
        raise ValueError(f"unsupported impact_flags: {unknown_flags}")
    if work_type in TASK_BUNDLE_UI_FIRST_WORK_TYPES and set(impact_flags) & set(TASK_BUNDLE_UI_FIRST_FLAGS):
        return "ui-first"
    return "standard"


def derive_task_bundle_required_docs(work_type: str, impact_flags: tuple[str, ...]) -> tuple[str, ...]:
    if work_type not in TASK_BUNDLE_WORK_TYPES:
        raise ValueError(f"unsupported work_type: {work_type}")
    if any(flag not in TASK_BUNDLE_IMPACT_FLAGS for flag in impact_flags):
        unknown_flags = sorted(flag for flag in impact_flags if flag not in TASK_BUNDLE_IMPACT_FLAGS)
        raise ValueError(f"unsupported impact_flags: {unknown_flags}")

    docs = set(TASK_BUNDLE_CORE_REQUIRED_DOCS)
    docs.update(TASK_BUNDLE_BASE_DOCS[work_type])

    if set(impact_flags) & set(TASK_BUNDLE_UX_SPEC_FLAGS):
        docs.update(TASK_BUNDLE_UI_REQUIRED_DOCS)
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
    if manifest.delivery_strategy not in TASK_BUNDLE_DELIVERY_STRATEGIES:
        errors.append(f"{task_root}: unsupported delivery_strategy: {manifest.delivery_strategy}")
    if manifest.execution_topology not in TASK_BUNDLE_EXECUTION_TOPOLOGIES:
        errors.append(f"{task_root}: unsupported execution_topology: {manifest.execution_topology}")
    if manifest.execution_topology in ("csv-fanout", "hybrid"):
        if manifest.orchestration is None:
            errors.append(f"{task_root}: csv-fanout/hybrid requires orchestration block")
        elif manifest.execution_topology == "csv-fanout":
            missing_orch_keys = sorted(
                key for key in TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS
                if key not in manifest.orchestration
            )
            if missing_orch_keys:
                errors.append(f"{task_root}: orchestration missing required keys: {missing_orch_keys}")
        fanout_docs = derive_csv_fanout_docs(manifest.execution_topology)
        missing_fanout_docs = sorted(doc for doc in fanout_docs if doc not in manifest.required_docs)
        if missing_fanout_docs:
            errors.append(f"{task_root}: required_docs missing csv-fanout docs: {missing_fanout_docs}")
    if manifest.execution_topology == "csv-fanout":
        work_items_dir = task_root / "work-items"
        if not work_items_dir.is_dir():
            errors.append(f"{task_root}: csv-fanout requires work-items/ directory")
        elif not list(work_items_dir.glob("*.csv")):
            errors.append(f"{task_root}: work-items/ must contain at least one .csv file")
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
    expected_docs.update(derive_csv_fanout_docs(manifest.execution_topology))
    missing_expected_docs = sorted(expected_docs - set(manifest.required_docs))
    if missing_expected_docs:
        errors.append(f"{task_root}: required_docs missing derived docs: {missing_expected_docs}")

    expected_delivery_strategy = decide_task_bundle_delivery_strategy(
        manifest.work_type,
        manifest.impact_flags,
    )
    if manifest.delivery_strategy != expected_delivery_strategy:
        errors.append(
            f"{task_root}: delivery_strategy mismatch: expected={expected_delivery_strategy!r} actual={manifest.delivery_strategy!r}"
        )

    expected_gate = decide_spec_validation_gate(manifest.impact_flags, manifest.required_docs)
    if manifest.validation_gate != expected_gate:
        errors.append(
            f"{task_root}: validation_gate mismatch: expected={expected_gate!r} actual={manifest.validation_gate!r}"
        )

    if manifest.source_of_truth.get("execution") != "EXECUTION_PLAN.md":
        errors.append(f"{task_root}: source_of_truth.execution must point to EXECUTION_PLAN.md")
    if manifest.source_of_truth.get("validation") != "SPEC_VALIDATION.md":
        errors.append(f"{task_root}: source_of_truth.validation must point to SPEC_VALIDATION.md")

    for source_key, source_path in TASK_BUNDLE_OPTIONAL_SOURCE_OF_TRUTH_PATHS.items():
        if source_key == "design_references":
            if "DESIGN_REFERENCES/" in manifest.required_docs and manifest.source_of_truth.get(source_key) != source_path:
                errors.append(f"{task_root}: source_of_truth.{source_key} must point to {source_path}")
            continue
        if source_path in manifest.required_docs and manifest.source_of_truth.get(source_key) != source_path:
            errors.append(f"{task_root}: source_of_truth.{source_key} must point to {source_path}")

    for source_key, relative_path in manifest.source_of_truth.items():
        source_path = task_root / relative_path
        if not source_path.exists():
            errors.append(f"{task_root}: source_of_truth.{source_key} points to missing file: {relative_path}")

    design_references_path = manifest.source_of_truth.get("design_references")
    if design_references_path:
        manifest_json_path = task_root / design_references_path
        if manifest_json_path.exists():
            try:
                design_references = json.loads(manifest_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{task_root}: invalid design reference manifest JSON: {design_references_path}: {exc}")
            else:
                if not isinstance(design_references, list) or not design_references:
                    errors.append(f"{task_root}: design reference manifest must contain at least one entry: {design_references_path}")

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
