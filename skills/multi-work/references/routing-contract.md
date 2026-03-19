# Multi Work Routing Contract

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| 기본 repo/code 탐색 | `explorer`, `structure-reviewer` |
| 외부 기술 판단/official docs 필요 | 기본 조합 + `web-researcher` |
| 브라우저 재현/시각 증거 필요 | 해당 조합 + `browser-explorer` |

최소 helper 수는 항상 2개다.

## Routing Matrix

| Condition | Route |
|-----------|-------|
| plan mode | `design-task` |
| 사용자가 계획/설계를 요청 | `design-task` |
| 승인된 task bundle의 다음 slice 실행 | `implement-task` |
| 새 작업이 크거나 모호함 | `design-task` |
| continuity 판단이나 bundle 생성이 필요함 | `design-task` |
| 작고 bounded한 작업 | direct execution |

`multi-work`는 top-level wrapper다.
실제 task bundle 설계/실행 세부 규칙은 각각 `design-task`, `implement-task` 계약을 그대로 따른다.

## Direct Execution Guardrail

- direct execution이어도 멀티 에이전트 탐색은 생략하지 않는다.
- `scripts/workflow_contract.py`의 slice budget 판단을 그대로 재사용한다.
- broad handoff면 `split-replan`이다.
- 허용 가능한 slice만 `small slices + run-to-boundary`로 진행한다.
- writer는 기존 writer 조건 충족 시에만 사용한다.
- 병렬 writer는 파일 경계가 분리되고 shared file 통합이 메인 스레드에 남을 때만 사용한다.
- active task bundle 후보가 여러 개면 `implement-task`의 candidate confirmation 규칙을 따른다.

## Review Boundary

- `multi-work`는 리뷰를 자동 실행하지 않는다.
- 멀티 에이전트 리뷰는 `multi-review` explicit step으로 분리한다.
