---
name: design-task
description: >
  Large or ambiguous task planning skill. Use when the user asks to "설계해줘", "계획 세워줘",
  "어떻게 쪼갤지 정리해줘", or explicitly asks for no code changes.
  Build or update tasks/{task-slug}/PLAN.md from repository evidence and user intent without modifying code.
---

# Workflow: Design Task

## Goal

사용자 요청을 구현 가능한 실행 슬라이스로 설계하고 `tasks/<task-slug>/PLAN.md`를 생성/갱신한다.
설계 단계에서는 코드 수정을 금지한다.

## Hard Rules

- 코드/설정/테스트 파일을 수정하지 않는다.
- read-only 탐색만 수행한다.
- 출력 경로는 항상 `tasks/<task-slug>/PLAN.md`를 사용한다.
- 기존 `PLAN.md`가 있으면 삭제/초기화하지 말고 현재 결정, 완료 맥락, 남은 리스크를 반영해 갱신한다.

## Inputs

- 사용자 요청
- 코드베이스 read-only 탐색 결과
- 사용자가 지정한 문서/경로
- 기존 `tasks/<task-slug>/PLAN.md`, `tasks/<task-slug>/STATUS.md` (있을 때)

## Task Slug Selection

1. 사용자 지정 slug/path가 있으면 그대로 사용한다.
2. 없으면 작업 제목을 hyphen-case로 정규화해 slug를 만든다.
3. 동명이인 slug가 이미 있으면 의미를 보존한 접미사(`-v2`, `-api`, `-ui`)를 붙인다.

## Workflow

1. 요청의 목표/제약/성공 기준을 추출한다.
2. 관련 코드와 문서를 read-only로 조사하고 근거를 수집한다.
3. `Planning lens`를 분류한다.
4. lens에 맞춰 planning role fan-out을 수행한다.
5. 작업 유형을 `feature`, `bugfix`, `refactor`, `prototype` 중 하나로 결정한다.
6. 변경 경계(유지/변경/금지)와 의사결정 공백을 분리한다.
7. 한 번의 구현 세션에서 검증 가능한 `Execution slices`를 작성한다.
8. 검증 전략과 stop/replan 조건을 명시한다.
9. `tasks/<task-slug>/PLAN.md`를 생성 또는 갱신한다.

## Multi-Agent Usage (Optional)

필요할 때만 read-only 병렬 에이전트를 사용한다. 설계 단계에서는 writer를 사용하지 않는다.

### Planning Roles (Internal-Only Priority)

planning role은 internal fan-out 전용이다.
user-facing install/projection 대상으로 취급하지 않는다.
아래 planning role을 내부 우선 순위로 사용한다.
- `web-researcher`
- `solution-analyst`
- `product-planner`
- `ux-journey-critic`
- `delivery-risk-planner`
- `prompt-systems-designer`

### Fallback Rules (Runtime Unavailable)

런타임에서 internal planning role이 직접 실행되지 않으면 아래 fallback을 사용한다.
- `web-researcher`: 메인 스레드에서 직접 웹 조사 수행 (출처 링크 + 날짜 + 사실/추정 구분)
- 나머지 planning role: `explorer` + role card overlay를 사용한다.
  - role card source: `${SKILL_DIR}/references/planning-role-cards.md`
- `architecture-reviewer`: 경계/모듈 영향 점검
- `type-specialist`: 공개 타입/계약 영향 점검
- `test-engineer`: 검증 시나리오 도출

### Planning Lens Classification

lens를 하나 이상 선택하고 해당 role을 fan-out한다.
- `external-benchmark`: 경쟁사/최신 대안 조사 (`web-researcher`)
- `solution-comparison`: 구현 옵션 비교 (`solution-analyst`)
- `product-clarification`: 목표/범위/수용 기준 정리 (`product-planner`)
- `ux-journey`: 사용자 흐름/마찰 점검 (`ux-journey-critic`)
- `delivery-risk`: 배포/운영 리스크 점검 (`delivery-risk-planner`)
- `prompt-system`: 프롬프트/도구 경계 설계 (`prompt-systems-designer`)

## PLAN Template (Fixed Sections)

항상 아래 순서의 섹션을 유지한다.

```markdown
# Goal
# Task Type
# Scope / Non-goals
# Keep / Change / Don't touch
# Evidence
# Decisions / Open questions
# Execution slices
# Verification
# Stop / Replan conditions
```

### Required Subsections

- `# Evidence`에는 아래를 반드시 포함한다.
  - `Repo evidence`
  - `External evidence` (오프라인/불필요/제약 시 `없음` 또는 사유를 명시)
  - `Options considered`
- `# Decisions / Open questions`에는 아래를 반드시 포함한다.
  - `Chosen approach`
  - `Rejected alternatives`
  - `Need user decision`

## Task Type Focus

- `feature`: 사용자 흐름, acceptance criteria, out-of-scope를 명확히 정의한다.
- `bugfix`: 재현 조건, 원인 가설, 회귀 방지 검증을 우선 정의한다.
- `refactor`: 유지 계약, 변경 경계, 회귀 위험을 우선 정의한다.
- `prototype`: 가설, 평가 기준, 폐기 가능한 범위를 명확히 정의한다.

## Output Quality Checklist

- 실행 슬라이스는 독립적으로 완료/검증 가능한 단위인가?
- 각 슬라이스에 완료 기준과 검증 항목이 있는가?
- 공개 경계 변경 여부가 명시되었는가?
- 즉시 중단 또는 재설계가 필요한 조건이 정의되었는가?
- 선택한 lens와 role fan-out 근거가 `Evidence`/`Decisions`에 반영되었는가?
