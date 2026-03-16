## 판정 흐름

1. 작업 유형과 규모를 평가한다.
2. Fast lane 조건을 모두 만족하면 메인 스레드가 직접 수정한다.
3. 그 외는 에이전트를 활용한다 (20-workflows.md 참조).

## Fast lane

아래 조건을 모두 만족하면 메인 스레드가 직접 수정한다.

- 변경이 1개 파일 범위로 제한됨
- 변경량이 소규모(diff가 작음)
- public API/schema/config/migration/shared type/cross-module boundary 변경이 없음
- 원인과 대상 파일이 명확함
- 검증을 1개 집중 체크로 마무리할 수 있음

## 위임 기본 규칙

- non-trivial 작업은 `design-task`/`implement-task` 경로를 사용한다.
- `small slices + run-to-boundary`를 기본으로 사용한다.
- slice budget(repo-tracked files 3개 이하, 순 diff 150 LOC 내외)을 넘는 handoff는 `split/replan before execution`으로 되돌린다.
- `wait timed_out` 시 허용 경로는 `longer wait -> optional queued status probe -> background or natural completion`이다. `queued-only` semantics다.
- Immediate status check requires explicit cancel path.

## Exit documentation review

- 모든 lane은 종료 전에 메인 스레드가 실질 영향이 있는 문서만 다시 탐색하고 검토한다.
- `docs/policy`, `skills`, `agent-registry` 같은 SSOT가 바뀌면 관련 generated projection sync와 대응 `--check`를 통과시킨 뒤 종료한다. <!-- repo-only -->
