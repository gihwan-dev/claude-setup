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
3. 작업 유형을 `feature`, `bugfix`, `refactor`, `prototype` 중 하나로 결정한다.
4. 변경 경계(유지/변경/금지)와 의사결정 공백을 분리한다.
5. 한 번의 구현 세션에서 검증 가능한 `Execution slices`를 작성한다.
6. 검증 전략과 stop/replan 조건을 명시한다.
7. `tasks/<task-slug>/PLAN.md`를 생성 또는 갱신한다.

## Multi-Agent Usage (Optional)

필요할 때만 read-only 병렬 에이전트를 사용한다.
- `explorer`: 코드/문서 증거 수집
- `architecture-reviewer`: 경계/모듈 영향 점검
- `type-specialist`: 공개 타입/계약 영향 점검
- `test-engineer`: 검증 시나리오 도출
설계 단계에서는 writer를 사용하지 않는다.

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
