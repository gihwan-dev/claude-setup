---
name: frontend-ui-state-decomposer
description: >
  Turn vague frontend feature requirements into an explicit UI state model, event transition map,
  component boundary plan, and pre-implementation test checklist.
  Use when designing a page, component, form, modal, table, onboarding flow, checkout flow, or dashboard interaction,
  especially when requirements are feature-oriented but the UI state model is not explicit,
  or when the user wants to identify edge cases before coding.
  Do not use for backend-only tasks, pure debugging, or when the UI state model is already fully specified and implementation-ready.
---

# Frontend UI State Decomposer

모호한 프론트엔드 요구사항을 구현 전 단계에서 상태 중심으로 분해한다. 상태/이벤트/경계를 먼저 명확히 해서 누락과 재작업을 줄인다.

## Language Rule

- Always respond in the user's language.
- Keep code identifiers, file paths, APIs, and commands in their original language.

## Workflow

1. Identify user intents and success criteria from the end-user perspective.
2. Determine the minimum required data and source of truth.
3. Enumerate UI states.
   - Always evaluate: initial, loading, refreshing, empty, partial, error, success, disabled, permission denied, offline, optimistic, stale.
   - Do not skip empty/error/loading states even when they look obvious.
   - Prefer fewer states and simpler transitions when possible. Merge redundant states with identical UI behavior.
4. Map events and state transitions.
5. Define component boundaries and responsibilities.
   - container vs presentational
   - server state vs client state
   - local state vs shared state
6. Call out accessibility, responsive behavior, localization, and performance constraints.
7. Produce edge cases and a test checklist.

## Required Output Format

Use the exact section order below:

1. User Intents
2. Success Criteria
3. Data Contract / Source of Truth
4. State Matrix
5. Events and Transitions
6. Component Breakdown
7. A11y / Responsive / Perf Constraints
8. Edge Cases
9. Test Checklist

## Output Constraints

- In `State Matrix`, include state name, entry condition, visible UI, blocked actions, and recovery path.
- In `Events and Transitions`, include event, source state, target state, guard, and side effects.
- If critical details are missing, add a short `Assumptions` subsection and continue.
- Keep outputs implementation-ready and framework-agnostic unless the user asked for a specific stack.

## Example Invocations

- `$frontend-ui-state-decomposer 페이지 요구사항이 아직 모호한데 UI 상태 모델, 이벤트 전이, 테스트 체크리스트를 먼저 만들어줘.`
- `$frontend-ui-state-decomposer 모달 기반 온보딩 플로우를 구현 전에 상태별 UI와 전이 조건으로 분해해줘.`
- `$frontend-ui-state-decomposer 대시보드 테이블(필터/정렬/새로고침/오프라인)의 edge case를 상태 중심으로 정리해줘.`
