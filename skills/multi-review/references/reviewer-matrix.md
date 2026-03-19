# Multi Review Matrix

## Target Precedence

1. user-specified path
2. user-specified commit or range
3. current worktree diff vs `HEAD`

## Baseline Reviewers

이 3개 reviewer는 항상 병렬 실행한다.

- `structure-reviewer`
- `code-quality-reviewer`
- `test-engineer`

## Conditional Reviewers

| Condition | Add reviewer |
|-----------|--------------|
| public surface changed / module boundary risk | `architecture-reviewer` |
| shared/public type changed / generics risk | `type-specialist` |
| React/TSX/frontend slice | `react-state-reviewer` |
| visual regression / browser repro needed | `browser-explorer` |

## Synthesis Contract

- 서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.
- 메인 에이전트는 reviewer fan-out 뒤 병렬로 개인 작업을 하지 않고, 필요한 후속 탐색은 결과를 받은 뒤 최소 범위로만 수행한다.
- 결과는 findings first, summary second다.
- findings는 severity 순으로 정렬한다.
- 가능한 경우 file/line 근거를 붙인다.
- open questions와 residual risk는 findings 뒤에 짧게 덧붙인다.
- 이 skill은 수정하지 않고 review만 수행한다.
