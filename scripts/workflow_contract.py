#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

LONG_RUNNING_PUBLIC_SURFACE = ("design-task", "implement-task")

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
)

CORE_HELPER_ORCHESTRATION_EXPECTED = {
    "worker": {
        "blocking_class": "blocking",
        "result_contract": "final-or-checkpoint",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "not-applicable",
    },
    "verification-worker": {
        "blocking_class": "semi-blocking",
        "result_contract": "final-or-checkpoint",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "explorer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "architecture-reviewer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "code-quality-reviewer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "type-specialist": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "test-engineer": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
    "module-structure-gatekeeper": {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "interrupt-drain-ack-close",
        "late_result_policy": "merge-if-relevant",
    },
}

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
        "사용자에게는 `design-task`, `implement-task`만 노출한다.",
        "각 slice는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "기본값: delegated lane 한 실행 단위(run)에서 정확히 하나의 `worker`가 code diff를 적용한다.",
        "single-writer 적용 단위는 run이 아니라 slice다. 각 slice의 code diff ownership은 fresh `worker` 1명이 담당한다.",
        "slice가 refactor/test/type-contract 성격을 가질 수 있어도 code diff를 적용하는 protocol-level writer는 항상 `worker`다.",
        "phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.",
        "`fork_context` 기본값은 `false`다. 축약 불가능한 컨텍스트 의존일 때만 `true`를 허용하고 이유를 `STATUS.md`에 기록한다.",
        "slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.",
        "공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.",
        "멀티에이전트 생명주기 경계는 `inactivity window`, `blocking deadline`, `drain grace` 3개로 고정한다. raw second(예: 90초/60초)는 정책 문구로 고정하지 않는다.",
        "stall 판정은 `communication liveness`와 `execution liveness`가 모두 끊긴 경우에만 허용한다.",
        "close 절차는 `liveness 확인 -> interrupt로 final/checkpoint flush 요청 -> drain grace 대기 -> 결과 ACK -> close_agent` 순서를 따른다.",
        "writer handoff brief에는 `blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`를 포함하고 raw second는 적지 않는다.",
        "core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.",
        "같은 slice에 두 번째 writer를 투입하지 않는다.",
        "partial diff가 남으면 오케스트레이터는 read-only로 확인만 하고 `STATUS.md`에 기록한 뒤 재설계한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.",
        "helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`)",
        "`structure-planner`는 아래 조건에서 `design-task` 내부 fan-out으로 실행한다.",
        "도메인과 무관하게 아래 조건 중 하나면 실행한다.",
        "`module-structure-gatekeeper`는 비trivial code diff 이후 실행한다.",
        "FAIL 판정은 공통 구조 관점에서 P1로 취급한다.",
        "`frontend-structure-gatekeeper`는 비trivial frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`) 이후 추가 실행한다.",
        "FAIL 판정은 React 구조 관점에서 P1로 취급한다.",
        "quality preflight/reviewer helper는 `품질판정: keep-local | promote-refactor | promote-architecture`를 포함한다.",
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
        "코드 수정은 `worker`만 수행한다.",
        "slice가 refactor/test/type-contract 성격을 가질 수 있어도 code diff를 적용하는 protocol-level writer는 항상 `worker`다.",
        "slice 실행 순서는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision`이다.",
        "phase 2 focused validation은 메인 스레드가 수행한다.",
        "phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.",
        "`PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.",
        "full-repo validation은 shared/public boundary 변경 시에만 허용한다.",
        "같은 slice에 두 번째 writer를 투입하지 않는다.",
        "멀티에이전트 생명주기 경계는 `inactivity window`, `blocking deadline`, `drain grace`다.",
        "worker 실패는 `상태: blocked`이거나 dual-signal inactivity 이후 drain grace 안에 `final/checkpoint`를 받지 못했을 때만 기록한다.",
        "advisory reviewer 미응답은 slice 실패로 처리하지 않고 background/advisory로 전환한다.",
        "`verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 취급하고 그 외에는 advisory로 취급한다.",
        "`blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`",
        "안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`module-structure-gatekeeper`는 비trivial code diff 이후 자동 reviewer로 실행한다.",
        "`frontend-structure-gatekeeper`는 비trivial frontend diff에서 추가 자동 reviewer로 실행한다.",
    ),
    "agent-registry/project-planner/instructions.md": (
        "이 long-running planning path는 `promote-refactor` 또는 `promote-architecture`가 확정된 경우에만 진행한다.",
        "`keep-local`이면 기존 fast/deep-solo/delegated lane으로 되돌리고 long-running path를 시작하지 않는다.",
        "기존 코드 작업이면 intent triage 성격의 quality preflight로 `keep-local` / `promote-refactor` / `promote-architecture`를 먼저 판정한다.",
        "기존 코드에 구조 냄새가 있으면 기능 구현보다 refactor 설계를 먼저 만든다.",
        "`promote-refactor` 설계는 제거할 로직/유지할 로직, 모듈 분리 경계, 허용 추상화/금지 추상화, 테스트 삭제/축소/이동/유지 기준, slice 순서와 slice별 focused verification 1개를 반드시 포함한다.",
        "`promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향 결정을 먼저 고정한다.",
        "이 구현 단계는 승인된 `PLAN.md` 기반 long-running 실행만 다룬다.",
        "기존 코드 대상 구현은 promoted planning path와 `PLAN.md` 없이 즉시 시작하지 않는다.",
        "planning role fan-out은 internal-only",
        "도메인과 무관하게 예상 diff가 150 LOC 이상이거나 예상 변경 파일이 2개 이상이거나 대상 기존 코드 파일이 soft limit 근접/초과면 `structure-planner`를 포함해 파일 분해안을 먼저 확정한다.",
        "각 slice는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "phase 1은 fresh `worker`의 edit-only 단계다.",
        "slice가 refactor/test/type-contract 성격을 가질 수 있어도 code diff를 적용하는 protocol-level writer는 항상 `worker`다.",
        "phase 2 focused validation은 메인 스레드가 수행한다.",
        "비trivial code diff slice면 `module-structure-gatekeeper`를 focused validation reviewer로 기본 포함한다.",
        "frontend slice면 `frontend-structure-gatekeeper`를 추가한다.",
        "phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.",
        "focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`--no-verify` 재시도까지 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.",
        "멀티에이전트 생명주기 경계는 `inactivity window`, `blocking deadline`, `drain grace`다.",
        "close 절차는 `liveness 확인 -> interrupt로 final/checkpoint flush 요청 -> drain grace 대기 -> 결과 ACK -> close_agent` 순서를 따른다.",
        "`worker` 실패는 `상태: blocked`이거나 dual-signal inactivity 이후 drain grace 안에 `final/checkpoint`가 없을 때만 기록한다.",
        "writer handoff brief에는 phase, file budget, validation owner, fork_context policy, `blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`, commit requirement/timing/fallback policy를 포함한다.",
    ),
    "agent-registry/worker/instructions.md": (
        "기본 역할은 edit-only다. handoff에 phase가 명시되지 않으면 코드 수정 외 검증/커밋을 수행하지 않는다.",
        "validation/commit은 handoff에 phase(`validation`, `commit-only`)가 명시된 경우에만 수행한다.",
        "`상태: final|checkpoint|blocked`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "interrupt/close 요청을 받으면 새 작업 시작을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `checkpoint`를 정확히 1회 flush한다.",
    ),
    "agent-registry/explorer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "interrupt/close 요청을 받으면 새 탐색 시작을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `preliminary`를 정확히 1회 flush한다.",
    ),
    "agent-registry/verification-worker/instructions.md": (
        "`상태: final|checkpoint|blocked`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "interrupt/close 요청을 받으면 새 로그 분석 시작을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `checkpoint`를 정확히 1회 flush한다.",
    ),
    "agent-registry/architecture-reviewer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
        "interrupt/close 요청을 받으면 새 리뷰 항목 확장을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `preliminary`를 정확히 1회 flush한다.",
    ),
    "agent-registry/code-quality-reviewer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
        "interrupt/close 요청을 받으면 새 리뷰 항목 확장을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `preliminary`를 정확히 1회 flush한다.",
    ),
    "agent-registry/type-specialist/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "interrupt/close 요청을 받으면 새 타입 분석 확장을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `preliminary`를 정확히 1회 flush한다.",
    ),
    "agent-registry/test-engineer/instructions.md": (
        "`상태: final|preliminary`",
        "`진행 상태: phase=<...>; last=<...>; next=<...>`",
        "`품질판정: keep-local | promote-refactor | promote-architecture`",
        "findings-first로 작성하고 품질판정과 핵심 결론을 먼저 제시한다.",
        "interrupt/close 요청을 받으면 새 테스트 케이스 확장을 중지하고 `final`을 우선 flush한다. `final`이 불가능하면 `preliminary`를 정확히 1회 flush한다.",
    ),
    "skills/implement-task/agents/openai.yaml": (
        "approved PLAN",
        "`worker`",
        "worker edit-only -> main focused validation -> same-worker commit-only",
        "STATUS.md",
        "blocking_class/result_contract/close_protocol/liveness_signals",
        "liveness 확인 -> interrupt flush -> drain grace -> ACK -> close_agent",
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
        "| 외부 리서치/경쟁사 벤치마킹 | explorer | web-researcher |",
        "| 솔루션 옵션 비교/트레이드오프 분석 | reviewer | solution-analyst |",
        "writer가 90초 동안 응답이 없으면 1회 interrupt로 상태 요약을 요청한다. 추가 60초 안에 요약이 없으면 slice 실패로 기록하고 stop/replan한다.",
        "자동 승격된 refactor slice의 기본 writer는 `refactoring-expert`다.",
        "테스트-only slice는 `qa-engineer`를 writer로 사용하고, public/shared type contract가 핵심인 slice는 `typescript-pro`를 writer로 사용한다.",
    ),
    "skills/implement-task/SKILL.md": (
        "keep-local",
        "refactoring-expert",
        "qa-engineer",
        "typescript-pro",
        "writer wait 90초 1회 발생 시 interrupt 1회로 상태 요약을 요청한다.",
        "interrupt 후 추가 60초 안에 요약이 없으면 slice 실패를 기록하고 stop/replan한다.",
        "timeout/recovery 실패(90초 대기 + interrupt 1회 + 추가 60초 내 요약 실패)",
    ),
    "skills/implement-task/agents/openai.yaml": (
        "keep-local",
        "refactoring-expert",
        "qa-engineer",
        "typescript-pro",
    ),
    "agent-registry/project-planner/instructions.md": (
        "writer 대기 90초가 발생하면 1회 interrupt로 상태 요약을 요청한다.",
        "interrupt 이후 추가 60초 안에 요약이 없으면 slice 실패를 기록하고 stop/replan한다.",
        "자동 승격된 refactor slice의 기본 writer는 `refactoring-expert`다.",
        "테스트-only slice는 `qa-engineer`, public/shared type contract가 핵심인 slice는 `typescript-pro`를 writer로 사용한다.",
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
