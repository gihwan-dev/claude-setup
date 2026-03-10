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
- quality preflight verdict와 근거를 반드시 기록한다.
- 이 skill 경로는 `promote-refactor` 또는 `promote-architecture`가 확정된 경우에만 진행한다. `keep-local`은 기존 lane으로 되돌리고 여기서 장기 실행 계획을 시작하지 않는다.
- 각 execution slice는 변경 경계, 예상 파일 수, validation owner, stop/replan 조건을 반드시 포함한다.
- slice 설계 기본 guardrail은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice로 묶는 giant mixed slice를 금지한다.

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
2. 관련 코드와 문서를 read-only로 조사하고 quality preflight 근거를 수집한다.
3. quality preflight verdict와 후속 경로를 기록한다.
4. 이 skill path는 `promote-refactor` 또는 `promote-architecture`일 때만 계속한다.
5. `Planning lens`를 분류한다.
6. lens에 맞춰 planning role fan-out을 수행한다.
7. 작업 유형을 `feature`, `bugfix`, `refactor`, `prototype` 중 하나로 결정한다.
8. 구조 냄새가 있으면 기능 설계보다 refactor 설계를 먼저 만든다.
9. `promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향 결정을 먼저 고정한 뒤 slice를 설계한다.
10. 변경 경계(유지/변경/금지)와 의사결정 공백을 분리한다.
11. 한 번의 구현 세션에서 검증 가능한 bounded `Execution slices`를 작성한다.
12. 검증 전략과 stop/replan 조건을 명시한다.
13. `tasks/<task-slug>/PLAN.md`를 생성 또는 갱신한다.

## Multi-Agent Usage (Optional)

필요할 때만 read-only 병렬 에이전트를 사용한다.

### Planning Roles (Internal-Only Priority)

planning role은 internal fan-out 전용이다.
user-facing install/projection 대상으로 취급하지 않는다.
아래 planning role을 내부 우선 순위로 사용한다.
- `web-researcher`
- `solution-analyst`
- `product-planner`
- `structure-planner`
- `ux-journey-critic`
- `delivery-risk-planner`
- `prompt-systems-designer`
- 기존 TS/JS/React 코드의 quality preflight는 `explorer`를 기본으로 사용한다.
- 구조 냄새가 보이면 `structure-planner`, `complexity-analyst`, `test-engineer`를 추가해 자동 승격 여부와 분해 경계를 먼저 정리한다.
- public/shared boundary 승격 신호가 보이면 `architecture-reviewer`를 fan-out해 `promote-architecture` 여부와 boundary 결정을 먼저 고정한다.

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
- `module-structure`: 공통 모듈 분해/책임 경계 설계 (`structure-planner`)
- `ux-journey`: 사용자 흐름/마찰 점검 (`ux-journey-critic`)
- `delivery-risk`: 배포/운영 리스크 점검 (`delivery-risk-planner`)
- `prompt-system`: 프롬프트/도구 경계 설계 (`prompt-systems-designer`)
- 기존 코드의 구조 냄새나 자동 승격 신호가 보이면 `module-structure` lens를 우선 선택하고 `complexity-analyst`, `test-engineer`를 함께 사용해 `promote-refactor` 여부를 확정한다.
- public/shared boundary 승격 신호가 보이면 `architecture-reviewer`를 fan-out해 `promote-architecture` 여부와 boundary/public/shared 영향을 먼저 확정한다.

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
  - `Quality preflight`
    - verdict (`keep-local` / `promote-refactor` / `promote-architecture`), 근거, 후속 경로를 기록한다.
- `# Execution slices`의 각 slice에는 아래를 반드시 포함한다.
  - `Change boundary`
  - `Expected files` (기본 `3개 이하` 또는 모듈 경계 예외 사유)
  - `Validation owner` (`main thread`)
  - `Focused validation plan` (`타깃 검증 1개 + 저비용 체크 1개`, full-repo 필요 시 사유)
  - `Stop / Replan trigger`

## Task Type Focus

- `feature`: 사용자 흐름, acceptance criteria, out-of-scope를 명확히 정의한다.
- `bugfix`: 재현 조건, 원인 가설, 회귀 방지 검증을 우선 정의한다.
- `refactor`: 유지 계약, 변경 경계, 회귀 위험을 우선 정의한다. 자동 승격된 리팩터링 계획은 아래 고정 산출물을 반드시 포함한다.
- `refactor`: 제거할 로직 / 유지할 로직
- `refactor`: 모듈 경계
- `refactor`: 허용 추상화 / 금지 추상화
- `refactor`: 테스트 삭제 / 축소 / 이동 / 유지 기준
- `refactor`: slice 순서와 slice별 focused verification 1개
- `prototype`: 가설, 평가 기준, 폐기 가능한 범위를 명확히 정의한다.

## Output Quality Checklist

- 실행 슬라이스는 독립적으로 완료/검증 가능한 단위인가?
- 각 슬라이스에 완료 기준과 검증 항목이 있는가?
- 각 슬라이스에 변경 경계/예상 파일 수/validation owner가 명시되었는가?
- 3-file/150 LOC guardrail을 넘길 때 모듈 경계 예외 사유가 기록되었는가?
- giant mixed slice 금지 조건을 회피하도록 설계되었는가?
- 공개 경계 변경 여부가 명시되었는가?
- 즉시 중단 또는 재설계가 필요한 조건이 정의되었는가?
- 선택한 lens와 role fan-out 근거가 `Evidence`/`Decisions`에 반영되었는가?
