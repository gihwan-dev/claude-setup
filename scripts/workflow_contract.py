#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

LONG_RUNNING_PUBLIC_SURFACE = ("design-task", "implement-task")
EXPECTED_CODEX_REASONING_EFFORT = "xhigh"

OrchestrationValue: TypeAlias = str | list[str]

WRITABLE_PROJECTION_AGENT_IDS = ("worker",)

DISABLED_WRITABLE_PROJECTION_AGENT_IDS = (
    "frontend-developer",
    "qa-engineer",
    "refactoring-expert",
    "typescript-pro",
    "storybook-specialist",
    "prompt-engineer",
    "project-planner",
)

DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS = ("monitor",)

STRONG_CLOSE_REASONS = ["explicit-cancel", "hard-deadline", "blocked"]
ADVISORY_TIMEOUT_POLICY = "background-no-close"
NON_ADVISORY_TIMEOUT_POLICY = "observe-and-status-ping"
INVALID_CLOSE_REASON = "result-no-longer-needed"
HELPER_CLOSE_ACK_DEFINITION = (
    "interrupt 이후 관측된 `preliminary`/`checkpoint`/`final` 출력 또는 "
    "drain grace 뒤 terminal runtime status transition"
)
TERMINAL_RUNTIME_STATUSES = (
    "blocked",
    "cancelled",
    "completed",
    "errored",
    "interrupted",
)

INTERNAL_PLANNING_ROLE_IDS = (
    "web-researcher",
    "solution-analyst",
    "product-planner",
    "structure-planner",
    "ux-journey-critic",
    "delivery-risk-planner",
    "prompt-systems-designer",
)

REQUIRED_HELPER_AGENT_IDS = (
    "worker",
    "explorer",
    "verification-worker",
    "architecture-reviewer",
    "code-quality-reviewer",
    "type-specialist",
    "test-engineer",
    "module-structure-gatekeeper",
    "frontend-structure-gatekeeper",
)

EXPECTED_CODEX_SANDBOX_BY_AGENT = {
    "worker": "workspace-write",
}

CORE_HELPER_ORCHESTRATION_EXPECTED: dict[str, dict[str, OrchestrationValue]] = {
    "worker": {
        "blocking_class": "blocking",
        "result_contract": "final-or-checkpoint",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "not-applicable",
        "timeout_policy": NON_ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "verification-worker": {
        "blocking_class": "semi-blocking",
        "result_contract": "final-or-checkpoint",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": NON_ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "explorer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "architecture-reviewer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "code-quality-reviewer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "type-specialist": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "test-engineer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "module-structure-gatekeeper": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
    "frontend-structure-gatekeeper": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": ADVISORY_TIMEOUT_POLICY,
        "allowed_close_reasons": STRONG_CLOSE_REASONS,
    },
}

ADVISORY_HELPER_AGENT_IDS = tuple(
    agent_id
    for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items()
    if expected["blocking_class"] == "advisory"
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


def _decision(action: str, snapshot: HelperCloseSnapshot, close_allowed: bool, rationale: str) -> HelperCloseDecision:
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

PLAN_SECTION_ORDER = (
    "Goal",
    "Task Type",
    "Scope / Non-goals",
    "Keep / Change / Don't touch",
    "Evidence",
    "Decisions / Open questions",
    "Execution slices",
    "Verification",
    "Stop / Replan conditions",
)

STATUS_SECTION_ORDER = (
    "Current slice",
    "Done",
    "Decisions made during implementation",
    "Verification results",
    "Known issues / residual risk",
    "Next slice",
)

LEGACY_MILESTONE_SKILL_NAMES = (
    "milestone",
    "milestone-execute",
    "milestone-runner",
    "milestone-update",
)

GENERATED_SKILL_MANIFEST_NAME = ".claude-setup-generated-skills.json"

REQUIRED_CONTRACT_PHRASES = {
    "INSTRUCTIONS.md": (
        "기존 코드 수정/리뷰/`계속해`/`다음 단계`/버그 수정/기능 추가 요청에는 lane 판정 전에 quality preflight를 먼저 수행한다.",
        "quality preflight 결과는 `keep-local` / `promote-refactor` / `promote-architecture` 셋 중 하나로 기록한다.",
        "구현 요청은 `keep-local`이면 기존 fast/deep-solo/delegated lane 규칙으로 처리하고 `design-task`/`implement-task` long-running path는 시작하지 않는다.",
        "`promote-refactor`면 `design-task` 성격의 리팩터링 계획을 먼저 만든 뒤 `implement-task` slice로 진행한다.",
        "`promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향을 먼저 고정한 뒤 slice를 설계한다.",
        "기존 코드의 long-running `design-task`/`implement-task` 경로는 `promote-refactor` 또는 `promote-architecture`일 때만 시작한다.",
        "TS/JS/React 기존 코드는 quality preflight에서 `explorer`를 기본으로 사용한다.",
        "구조 냄새가 보이면 `complexity-analyst`, `structure-planner`, `test-engineer`를 추가하고, public/shared boundary 변경이 예상될 때만 `architecture-reviewer`를 붙인다.",
        "delegated lane의 code diff는 단일 writer만 허용하고 writable projection은 `worker`만 사용한다.",
        "delegated lane의 code diff는 정확히 하나의 `worker`만 적용한다.",
        "writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.",
        "`implement-task` long-running path는 single-writer delegated flow를 유지한다.",
        "각 slice는 `worker edit -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.",
        "slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.",
        "공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.",
        "늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.",
        "`monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection은 만들지 않는다.",
        "helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)는 runtime helper로 보장되어야 하며 각 `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)을 SSOT로 유지한다.",
        "`structure-planner`는 아래 조건에서 `design-task` 내부 fan-out으로 실행한다.",
        "도메인과 무관하게 아래 조건 중 하나면 실행한다.",
        "`module-structure-gatekeeper`는 비trivial code diff 이후 실행한다.",
        "FAIL 판정은 공통 구조 관점에서 P1로 취급한다.",
        "`frontend-structure-gatekeeper`는 비trivial frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`) 이후 추가 실행한다.",
        "FAIL 판정은 React 구조 관점에서 P1로 취급한다.",
        "quality preflight/reviewer helper는 `품질판정: keep-local | promote-refactor | promote-architecture`를 포함한다.",
        "작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.",
    ),
    "README.md": (
        "core helper 생명주기 정책: 각 helper `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)",
        "설치되는 agent projection에서 writable 예외는 `worker` 하나뿐이다. 나머지 generated agent는 read-only helper/reviewer만 유지한다.",
        "`monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection을 만들지 않는다.",
        "managed runtime agent preflight(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)",
        "작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.",
        "advisory helper close preflight에서는 `result가 더 이상 필요 없음`과 `wait timed_out -> status running -> no result -> close`를 종료 근거로 인정하지 않는다.",
    ),
    "CONTRIBUTING.md": (
        "`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`의 생명주기 메타데이터는 각 `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)이 SSOT다.",
        "설치되는 agent projection에서 writable 예외는 `worker` 하나뿐이다. 나머지 generated agent는 read-only helper/reviewer만 유지한다.",
        "`monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection을 만들지 않는다.",
        "작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.",
        "advisory helper close preflight에서는 `result가 더 이상 필요 없음`과 `wait timed_out -> status running -> no result -> close`를 종료 근거로 인정하지 않는다.",
    ),
    "skills/design-task/SKILL.md": (
        "이 skill 경로는 `promote-refactor` 또는 `promote-architecture`가 확정된 경우에만 진행한다.",
        "`promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향 결정을 먼저 고정한 뒤 slice를 설계한다.",
        "`Quality preflight`",
        "verdict (`keep-local` / `promote-refactor` / `promote-architecture`), 근거, 후속 경로를 기록한다.",
        "planning role은 internal fan-out 전용이다.",
        "user-facing install/projection 대상으로 취급하지 않는다.",
        "각 execution slice는 변경 경계, 예상 파일 수, validation owner, stop/replan 조건을 반드시 포함한다.",
        "slice 설계 기본 guardrail은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`다.",
    ),
    "skills/implement-task/SKILL.md": (
        "이 스킬은 승인된 `PLAN.md` 기반 long-running 실행만 다룬다.",
        "`implement-task`의 code writer는 `worker` 하나다.",
        "writable projection은 `worker`만 허용한다.",
        "focused validation은 메인 스레드가 수행한다.",
        "phase 1을 수행한 same `worker`가 commit-only로 재개한다.",
        "`PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.",
        "full-repo validation은 shared/public boundary 변경 시에만 허용한다.",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.",
        "늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "`verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 취급하고 그 외에는 advisory로 취급한다.",
        "안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`module-structure-gatekeeper`는 비trivial code diff 이후 자동 reviewer로 실행한다.",
        "`frontend-structure-gatekeeper`는 비trivial frontend diff에서 추가 자동 reviewer로 실행한다.",
        "작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.",
    ),
    "agent-registry/project-planner/instructions.md": (
        "이 long-running planning path는 `promote-refactor` 또는 `promote-architecture`가 확정된 경우에만 진행한다.",
        "`keep-local`이면 기존 fast/deep-solo/delegated lane으로 되돌리고 long-running path를 시작하지 않는다.",
        "기존 코드 작업이면 intent triage 성격의 quality preflight로 `keep-local` / `promote-refactor` / `promote-architecture`를 먼저 판정한다.",
        "**strategy-only 오케스트레이션** — 오케스트레이터는 전략/결정/통합을 담당하며 직접 code diff를 적용하지 않는다.",
        "**single-writer 유지** — writable projection은 `worker`만 허용하고 slice마다 정확히 한 명만 code diff를 적용한다.",
        "각 slice는 `worker edit -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "phase 1은 fresh `worker`의 edit-only 단계다.",
        "phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.",
        "늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "기존 코드에 구조 냄새가 있으면 기능 구현보다 refactor 설계를 먼저 만든다.",
        "`promote-refactor` 설계는 제거할 로직/유지할 로직, 모듈 분리 경계, 허용 추상화/금지 추상화, 테스트 삭제/축소/이동/유지 기준, slice 순서와 slice별 focused verification 1개를 반드시 포함한다.",
        "`promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향 결정을 먼저 고정한다.",
        "이 구현 단계는 승인된 `PLAN.md` 기반 long-running 실행만 다룬다.",
        "기존 코드 대상 구현은 promoted planning path와 `PLAN.md` 없이 즉시 시작하지 않는다.",
        "planning role fan-out은 internal-only",
        "도메인과 무관하게 예상 diff가 150 LOC 이상이거나 예상 변경 파일이 2개 이상이거나 대상 기존 코드 파일이 soft limit 근접/초과면 `structure-planner`를 포함해 파일 분해안을 먼저 확정한다.",
        "phase 2 focused validation은 메인 스레드가 수행한다.",
        "비trivial code diff slice면 `module-structure-gatekeeper`를 focused validation reviewer로 기본 포함한다.",
        "frontend slice면 `frontend-structure-gatekeeper`를 추가한다.",
        "focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`--no-verify` 재시도까지 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.",
        "writer handoff brief에는 phase, file budget, validation owner, `blocking_class`, `result_contract`, `close_protocol`, `timeout_policy`, `allowed_close_reasons`, `liveness_signals`, commit requirement/timing/fallback policy를 포함한다.",
        "작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.",
    ),
    "agent-registry/worker/instructions.md": (
        "기본 역할은 edit-only다. handoff에 phase가 명시되지 않으면 코드 수정 외 검증/커밋을 수행하지 않는다.",
        "validation/commit은 handoff에 phase(`validation`, `commit-only`)가 명시된 경우에만 수행한다.",
        "writer stall 기본 정책은 대기+점검이며 replacement writer는 허용하지 않는다.",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "`상태: final|checkpoint|blocked`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
    ),
    "agent-registry/explorer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
    ),
    "agent-registry/verification-worker/instructions.md": (
        "`상태: final|checkpoint|blocked`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "메인 검증이 끝났다는 사실만으로 close하지 않는다. 요약 결과 전달 또는 강한 종료 근거가 있어야 close를 판단한다.",
    ),
    "agent-registry/architecture-reviewer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
    ),
    "agent-registry/code-quality-reviewer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
    ),
    "agent-registry/type-specialist/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
    ),
    "agent-registry/test-engineer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
    ),
    "agent-registry/module-structure-gatekeeper/instructions.md": (
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
    ),
    "agent-registry/frontend-structure-gatekeeper/instructions.md": (
        "`wait timeout`은 stalled와 동일하지 않다.",
        "`liveness gate`와 `completion gate`를 분리한다.",
        "close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.",
        "`result가 더 이상 필요 없음`은 close 근거가 아니다.",
        "advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.",
        "advisory helper 미응답은 close가 아니라 background/advisory로 전환한다.",
        "`wait timed_out -> status running -> no result -> close`는 invalid sequence다.",
    ),
    "skills/implement-task/agents/openai.yaml": (
        "worker edit-only",
        "same-worker commit-only",
        "작은/저위험 slice는 메인 수동 리뷰를 우선하고 advisory helper는 `wait timed_out -> status running -> no result -> close` 같은 invalid sequence 없이 background/advisory로 다루면서 STATUS.md를 갱신해",
        "STATUS.md",
    ),
    "skills/design-task/agents/openai.yaml": (
        "Quality preflight",
        "promote-architecture",
        "architecture-reviewer",
        "change boundary, file budget, validation owner, and stop/replan conditions",
    ),
}

FORBIDDEN_CONTRACT_PHRASES = {
    "INSTRUCTIONS.md": (
        "long-running `implement-task` 경로에서도 코드 변경과 `STATUS.md` 갱신은 메인 스레드가 직접 수행한다.",
        "`implement-task` long-running path는 writable sub-agent를 사용하지 않는다.",
        "writable implementation agent는 user-facing install/projection 대상이 아니다.",
    ),
    "README.md": (
        "설치되는 agent projection은 read-only helper/reviewer만 유지하고, 코드 수정은 메인 스레드가 직접 수행한다.",
    ),
    "CONTRIBUTING.md": (
        "설치되는 agent projection은 read-only helper/reviewer만 유지하고, 코드 수정은 메인 스레드가 직접 수행한다.",
    ),
    "skills/implement-task/SKILL.md": (
        "`implement-task`의 code writer는 메인 스레드 하나다.",
        "`implement-task`는 writable sub-agent를 사용하지 않는다.",
        "메인 스레드가 현재 slice의 코드 변경을 직접 수행한다.",
    ),
    "skills/implement-task/agents/openai.yaml": (
        "메인 스레드에서 직접 진행해",
    ),
    "agent-registry/project-planner/instructions.md": (
        "**main-thread execution** — long-running path에서도 코드 수정과 상태 갱신은 메인 스레드가 직접 수행한다.",
        "코드 변경과 `STATUS.md` 갱신은 현재 메인 스레드가 직접 수행한다.",
        "writable sub-agent는 사용하지 않는다.",
    ),
}


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
