---
name: multi-review
description: >
  Explicit multi-agent review entry for the current diff or a user-specified
  target.
---

# Multi Review

작업 완료 후 명시적으로 호출하는 멀티 에이전트 리뷰 진입점이다.
기본 reviewer 3개를 항상 병렬로 실행하고, 필요 조건이 있을 때만 추가 reviewer를 붙인다.

## Trigger

- `/multi-review`
- `$multi-review`
- `multi-review`

## Hard Rules

- 기본은 read-only review다. 코드를 수정하지 않는다.
- 멀티 에이전트 reviewer fan-out이 불가능한 런타임이면 단일 리뷰로 축소하지 말고 blocked로 보고한다.
- 서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.
- 메인 에이전트는 reviewer fan-out 뒤 병렬로 개인 작업을 하지 않고, 필요한 후속 탐색은 결과를 받은 뒤 최소 범위로만 수행한다.
- reviewer fan-out은 `${SKILL_DIR}/references/reviewer-matrix.md`와 workflow helper 기준을 따른다.
- 기본 리뷰 대상은 current worktree diff 대 `HEAD`다.
- 사용자가 path, commit, range를 지정하면 그 대상을 우선한다.
- 결과는 반드시 findings first, summary second 형식으로 종합한다.

## Workflow

1. `${SKILL_DIR}/references/reviewer-matrix.md`를 읽고 리뷰 대상을 고정한다.
2. baseline reviewer를 항상 병렬 실행하고, 추가 reviewer는 diff 성격에 따라 붙인다.
3. reviewer fan-out 후에는 결과가 돌아올 때까지 `wait`/결과 수집만 수행하고, 메인 에이전트의 추가 파일 읽기나 검색은 중단한다.
4. reviewer 결과를 severity 순으로 정리하고 file/line 근거를 붙인다.
5. findings를 먼저 제시한 뒤, 필요한 경우에만 짧은 요약과 residual risk를 덧붙인다.

## Required References

- reviewer fan-out matrix, target precedence, synthesis contract: `${SKILL_DIR}/references/reviewer-matrix.md`

## Validation

- baseline reviewer 3개가 항상 포함됐는지 확인한다.
- reviewer fan-out 후 결과 수집 전까지 메인 에이전트가 추가 파일 읽기/검색을 하지 않았는지 확인한다.
- frontend diff면 `react-state-reviewer`가 추가됐는지 확인한다.
- public/shared contract 리스크가 있으면 `architecture-reviewer` 또는 `type-specialist`가 추가됐는지 확인한다.
- 결과가 findings first, summary second를 지키는지 확인한다.
