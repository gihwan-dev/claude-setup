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
    "type-specialist",
    "test-engineer",
)

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
        "사용자에게는 `design-task`, `implement-task`만 노출한다.",
        "각 slice는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.",
        "`fork_context` 기본값은 `false`다. 축약 불가능한 컨텍스트 의존일 때만 `true`를 허용하고 이유를 `STATUS.md`에 기록한다.",
        "slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.",
        "공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.",
        "writer가 90초 동안 응답이 없으면 1회 interrupt로 상태 요약을 요청한다. 추가 60초 안에 요약이 없으면 slice 실패로 기록하고 stop/replan한다.",
        "같은 slice에 두 번째 writer를 투입하지 않는다.",
        "partial diff가 남으면 오케스트레이터는 read-only로 확인만 하고 `STATUS.md`에 기록한 뒤 재설계한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.",
        "helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `type-specialist`, `test-engineer`)",
        "`structure-planner`는 아래 조건에서 `design-task` 내부 fan-out으로 실행한다.",
        "`frontend-structure-gatekeeper`는 비trivial frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`) 이후 실행한다.",
        "FAIL 판정은 frontend 구조 관점에서 P1로 취급한다.",
    ),
    "skills/design-task/SKILL.md": (
        "planning role은 internal fan-out 전용이다.",
        "user-facing install/projection 대상으로 취급하지 않는다.",
        "각 execution slice는 변경 경계, 예상 파일 수, validation owner, stop/replan 조건을 반드시 포함한다.",
        "slice 설계 기본 guardrail은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`다.",
    ),
    "skills/implement-task/SKILL.md": (
        "slice 실행 순서는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision`이다.",
        "phase 2 focused validation은 메인 스레드가 수행한다.",
        "phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.",
        "`PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.",
        "full-repo validation은 shared/public boundary 변경 시에만 허용한다.",
        "같은 slice에 두 번째 writer를 투입하지 않는다.",
        "안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
    ),
    "agent-registry/project-planner/instructions.md": (
        "planning role fan-out은 internal-only",
        "각 slice는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 순서를 따른다.",
        "phase 2 focused validation은 메인 스레드가 수행한다.",
        "phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.",
        "focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`--no-verify` 재시도까지 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.",
        "writer handoff brief에는 phase, file budget, validation owner, fork_context policy, timeout policy, commit requirement/timing/fallback policy를 포함한다.",
    ),
    "agent-registry/worker/instructions.md": (
        "기본 역할은 edit-only다. handoff에 phase가 명시되지 않으면 코드 수정 외 검증/커밋을 수행하지 않는다.",
        "validation/commit은 handoff에 phase(`validation`, `commit-only`)가 명시된 경우에만 수행한다.",
    ),
    "skills/implement-task/agents/openai.yaml": (
        "writer edit-only -> main focused validation -> same-writer commit-only",
        "STATUS.md",
    ),
    "skills/design-task/agents/openai.yaml": (
        "change boundary, file budget, validation owner, and stop/replan conditions",
    ),
}

FORBIDDEN_CONTRACT_PHRASES = {
    "INSTRUCTIONS.md": (
        "| 외부 리서치/경쟁사 벤치마킹 | explorer | web-researcher |",
        "| 솔루션 옵션 비교/트레이드오프 분석 | reviewer | solution-analyst |",
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
