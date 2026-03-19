<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Run: python3 scripts/sync_instructions.py -->

# 멀티 에이전트 오케스트레이션 정책

## 핵심 원칙

- 메인 스레드는 의사결정과 구현에 집중한다. 대규모 코드 작성 위임은 writer 조건을 따른다.
- 조사/리뷰는 에이전트에 적극 위임하고 병렬 활용한다.
- 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 에이전트 카탈로그

| ID | 역할 | 도구 | 언제 소환하나 |
|----|------|------|-------------|
| `explorer` | 코드베이스 탐색/증거 수집 | Read, Grep, Glob | 원인/소유 영역 불명확, 탐색 필요 |
| `browser-explorer` | 브라우저 재현/시각 QA | Read, Bash, Grep, Glob | live browser reproduction, DOM/visual QA 필요 |
| `web-researcher` | 외부 문서/벤치마크 조사 | Read, Grep, Glob, WebFetch, WebSearch | 외부 docs, 벤치마크, official vendor docs 필요 |
| `code-quality-reviewer` | 코드 품질 리뷰 | Read, Write, Edit, Bash, Grep | 3+ 파일 변경, 보안/에러 로직, 명시적 요청 |
| `structure-reviewer` | 구조/복잡도 리뷰 + 분해 계획 | Read, Bash, Grep, Glob | non-trivial diff 후 항상 |
| `architecture-reviewer` | 경계/레이어/public surface 리뷰 | Read, Grep, Glob | public surface 또는 모듈 경계 변경 |
| `type-specialist` | 타입 계약 안정성 리뷰 | Read, Grep, Glob | shared/public type, generics 변경 |
| `react-state-reviewer` | React 상태 관리 리뷰 | Read, Grep, Glob | React/TSX 파일 변경, frontend slice |
| `test-engineer` | 테스트 품질 심사/회귀 리스크 | Read, Grep, Glob | 테스트 코드 변경·추가 또는 회귀 리스크 |
| `verification-worker` | 검증 결과 분석 | Read, Grep, Glob | 검증 로그가 noisy하거나 multi-step |
| `writer` | 범위 제한 코드 작성 | Read, Write, Edit, Bash, Grep, Glob | 대규모 변경에서 파일 경계가 명확한 위임 작성 |

## 에이전트 응답 포맷

- 필수: 핵심결론, 근거
- 선택: 리스크, 권장 다음 행동

## 언어

- 한국어 기본, 코드 식별자는 원어

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
- read-only 조사/탐색/외부 리서치/브라우저 재현이 핵심 작업이 아님

## 위임 기본 규칙

- non-trivial 작업은 `design-task`/`implement-task` 경로를 사용한다.
- `small slices + run-to-boundary`를 기본으로 사용한다.
- slice budget(repo-tracked files 3개 이하, 순 diff 150 LOC 내외)을 넘는 handoff는 `split/replan before execution`으로 되돌린다.
- read-only 탐색/리서치/브라우저 재현은 각각 `explorer`/`web-researcher`/`browser-explorer`가 담당한다. 메인 스레드는 결과만 통합하고, helper unavailable이면 blocked로 보고한다.

## Writer 위임 조건

아래 조건을 모두 만족하면 writer 에이전트에 코드 작성을 위임한다.

- 변경 대상 파일이 2개 이상이고 파일 경계가 명확함
- `target_path`로 수정 범위를 한정할 수 있음
- shared file(barrel exports, route, config) 수정이 불필요하거나 integrator 역할로 분리 가능
- 메인 스레드의 컨텍스트 소모가 큰 대규모 작업
- 병렬 writer가 필요한 경우 파일 간 의존이 없음

위임하지 않는 경우:
- Fast lane 대상 (1파일, 소규모)
- 아키텍처 결정이 필요한 불확실한 변경
- shared file만 수정하는 경우

## Exit documentation review

- 모든 lane은 종료 전에 메인 스레드가 실질 영향이 있는 문서만 다시 탐색하고 검토한다.
- `docs/policy`, `skills`, `agent-registry` 같은 SSOT가 바뀌면 관련 generated projection sync와 대응 `--check`를 통과시킨 뒤 종료한다. <!-- repo-only -->

## 작업별 에이전트 매핑

| 작업 유형 | 조사 단계 | 구현 단계 | 리뷰 단계 |
|-----------|----------|----------|----------|
| 기능 구현 | explorer, web-researcher | main-thread, [writer] | code-quality-reviewer, structure-reviewer, [architecture-reviewer], [type-specialist], [react-state-reviewer], test-engineer |
| 버그 수정 | explorer, [browser-explorer] | main-thread, [writer] | code-quality-reviewer, [react-state-reviewer], test-engineer |
| 리팩토링 | explorer, structure-reviewer | main-thread, [writer] | structure-reviewer, [architecture-reviewer], [react-state-reviewer], code-quality-reviewer |
| 코드 리뷰 | explorer | — | code-quality-reviewer, structure-reviewer, architecture-reviewer, type-specialist, [react-state-reviewer] |
| 리서치 | explorer, web-researcher, [browser-explorer] | — | — |
| 프로토타이핑 | web-researcher | main-thread | [verification-worker] |
| 문서 작업 | explorer | main-thread | — |

[대괄호] = 조건부 (해당 조건일 때만)

## 리뷰 자동 트리거

| 리뷰어 | 트리거 조건 |
|--------|------------|
| code-quality-reviewer | 3+ 파일 변경 or 보안/에러 로직 or 명시적 요청 |
| structure-reviewer | non-trivial diff 후 항상 |
| architecture-reviewer | public surface or 모듈 경계 변경 |
| type-specialist | shared/public type, generics 변경 |
| react-state-reviewer | React/TSX 파일 변경 + frontend slice |
| test-engineer | 테스트 코드 변경·추가 or 회귀 리스크 or 테스트 커버리지 공백 |

## 실행 흐름

### Fast lane

1. 최소 파일 확인
2. diff 적용
3. 검증
4. 보고

### Delegated flow

1. 조사 helper가 필요한 read-only 근거를 수집한다.
2. 메인 스레드는 조사 결과를 통합해 의사결정한다.
3. 구현 (`small slices + run-to-boundary`)
   - 메인 스레드 직접 작성 (기본)
   - writer 위임 (대규모, 파일 경계 명확)
   - 병렬 writer (worktree isolation, 파일 간 무의존)
4. 메인 스레드 focused validation + shared file 통합
5. 리뷰 에이전트
6. 결과 통합
