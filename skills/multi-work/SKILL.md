---
name: multi-work
description: >
  Explicit multi-agent work entry that explores first and routes to planning,
  task-bundle execution, or direct execution.
---

# Multi Work

일반 작업 요청의 기본 진입점이다.
항상 멀티 에이전트 탐색부터 시작하고, 그 결과를 바탕으로 계획, task-bundle 실행, 직접 실행 중 하나로 라우팅한다.

## Trigger

- `/multi-work`
- `$multi-work`
- `multi-work`

## Hard Rules

- 항상 멀티 에이전트 탐색부터 시작한다. 최소 helper 2개를 사용한다.
- 런타임에서 멀티 에이전트 fan-out이 불가능하면 single-agent로 축소하지 말고 blocked로 보고한다.
- 서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.
- 메인 에이전트는 helper fan-out 뒤 병렬로 개인 작업을 하지 않고, 필요한 후속 탐색은 결과를 받은 뒤 최소 범위로만 수행한다.
- plan mode에서는 read-only 탐색 후 계획만 산출한다.
- direct execution lane이어도 탐색 없이 바로 구현하지 않는다.
- slice/writer 판단은 `policy/workflow.toml`, `scripts/workflow_contract.py`, 기존 `design-task`/`implement-task` 계약을 그대로 따른다.
- 리뷰는 자동 실행하지 않는다. 멀티 에이전트 리뷰는 별도 `multi-review` explicit 호출로 분리한다.

## Workflow

1. `${SKILL_DIR}/references/routing-contract.md`를 읽고 요청 유형에 맞는 helper 조합을 선택한다.
2. 항상 멀티 에이전트 탐색부터 수행한다.
3. helper fan-out 후에는 결과가 돌아올 때까지 `wait`/결과 수집만 수행하고, 메인 에이전트의 추가 파일 읽기나 검색은 중단한다.
4. plan mode, 승인된 task bundle, direct execution 조건 판정은 helper 결과를 받은 뒤 routing contract와 workflow helper 기준을 그대로 따른다.
5. `design-task` 또는 `implement-task`로 라우팅될 때는 각 스킬의 세부 계약을 그대로 따른다.
6. direct execution lane에서도 `split-replan`, `small slices + run-to-boundary`, writer 기준을 기존 workflow helper 그대로 적용한다.
7. direct execution lane 종료 후 리뷰가 필요하면 `multi-review`를 명시적으로 안내한다.

## Required References

- helper matrix, routing matrix, direct execution guardrail: `${SKILL_DIR}/references/routing-contract.md`
- long-running planning/task-bundle 설계 계약: `skills/design-task/SKILL.md`
- 승인된 task bundle 실행 계약: `skills/implement-task/SKILL.md`

## Validation

- helper set에 최소 2개 agent가 포함됐는지 확인한다.
- helper fan-out 후 결과 수집 전까지 메인 에이전트가 추가 파일 읽기/검색을 하지 않았는지 확인한다.
- plan mode에서는 read-only planning만 수행했는지 확인한다.
- direct execution lane에서도 `split-replan`과 writer threshold가 유지되는지 확인한다.
- direct execution lane closeout에서 리뷰를 자동 실행하지 않았는지 확인한다.
