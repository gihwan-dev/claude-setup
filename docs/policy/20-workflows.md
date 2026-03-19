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

1. explorer/web-researcher 조사
2. 메인 의사결정
3. 구현 (`small slices + run-to-boundary`)
   - 메인 스레드 직접 작성 (기본)
   - writer 위임 (대규모, 파일 경계 명확)
   - 병렬 writer (worktree isolation, 파일 간 무의존)
4. 메인 스레드 focused validation + shared file 통합
5. 리뷰 에이전트
6. 결과 통합
