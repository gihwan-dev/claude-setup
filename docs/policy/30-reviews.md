## 리뷰와 planning role

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| main-thread | 쓰기 가능 | 전략, focused validation, 상태 통합/기록 |
| worker | 읽기/쓰기 | delegated lane과 `implement-task` slice의 유일한 code diff writer |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | quality preflight 승격 판정과 구조/검증 게이트 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## Internal Planning Roles

- `web-researcher`, `solution-analyst`, `product-planner`, `structure-planner`, `ux-journey-critic`, `delivery-risk-planner`, `prompt-systems-designer`
- 위 role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- 장시간 대기/폴링 감시는 built-in `monitor`만 사용하고 repo-managed projection은 만들지 않는다.

## 자동 리뷰 트리거

- reviewer는 지적 전용이 아니라 quality preflight 승격 판정과 focused gate를 담당한다.
- quality preflight에서 TS/JS/React 기존 코드는 `explorer`를 기본으로 붙인다.
- 구조 냄새가 있으면 `complexity-analyst`, `structure-planner`, `test-engineer`를 추가한다.
- `architecture-reviewer`는 public/shared boundary 예상 시에만 붙인다.
- `code-quality-reviewer`는 아래 중 하나라도 만족할 때만 실행한다.
  - 변경 파일이 3개 이상
  - 테스트가 추가되거나 변경됨
  - 에러 처리/동시성/보안 민감 로직이 변경됨
  - 사용자가 명시적으로 리뷰를 요청함
- `architecture-reviewer`는 아래 중 하나라도 만족하면 실행한다.
  - 변경 파일 7개 이상
  - 모듈/패키지 경계 2개 이상 변경
  - public surface 변경 (export, entrypoint, 핵심 설정)
- `structure-planner`는 아래 조건에서 `design-task` 내부 fan-out으로 실행한다.
  - 예상 diff가 150 LOC 이상인 경우
  - 예상 변경 파일이 2개 이상인 경우
  - 대상 기존 코드 파일이 soft limit에 근접하거나 초과해 분해 설계가 필요한 경우
- `module-structure-gatekeeper`는 비trivial code diff 이후 실행한다.
  - FAIL 판정은 공통 구조 관점에서 P1로 취급한다.
- `frontend-structure-gatekeeper`는 비trivial frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`) 이후 추가 실행한다.
  - FAIL 판정은 React 구조 관점에서 P1로 취급한다.
- `type-specialist`는 shared/public types, generics, public contract 변경 시 실행한다.
- `test-engineer`는 회귀 리스크가 크거나 테스트 커버리지 공백이 있을 때 실행한다.

## 서브 에이전트 응답 가이드라인

- quality preflight/reviewer helper는 `품질판정: keep-local | promote-refactor | promote-architecture`를 포함한다.
- 필수 항목은 `핵심결론`, `근거`다.
- 선택 항목은 `리스크`, `권장 다음 행동`, `추가 확인 필요`다.
- 원문 출력이 필요하면 최소 발췌만 포함하고 소스 경로를 명시한다.
