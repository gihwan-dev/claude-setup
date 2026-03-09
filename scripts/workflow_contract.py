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
        "각 slice는 `구현 -> 검증 -> 커밋 -> STATUS 갱신 -> 다음 slice 판정` 순서를 따른다.",
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
    ),
    "skills/implement-task/SKILL.md": (
        "`PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.",
        "안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
    ),
    "agent-registry/project-planner/instructions.md": (
        "planning role fan-out은 internal-only",
        "focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.",
        "hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.",
        "`--no-verify` 재시도까지 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.",
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
