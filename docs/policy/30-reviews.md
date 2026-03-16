## 리뷰와 planning role

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| main-thread | 쓰기 가능 | 전략, focused validation, 상태 통합/기록 |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | quality preflight 승격 판정과 구조/검증 게이트 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## Planning Roles

- `web-researcher`, `solution-analyst`, `product-planner`, `structure-planner`, `ux-journey-critic`, `delivery-risk-planner`, `prompt-systems-designer`
- planning role은 `design-task` 내부 fan-out 우선이며, 독립 호출도 가능하다.
- 장시간 대기/폴링 감시는 built-in `monitor`만 사용한다.
- UI 영향 long-running planning은 `ux-journey-critic`를 mandatory 기본값으로 두고, `product-planner`, `web-researcher`, `solution-analyst`, `structure-planner`, `architecture-reviewer`만 goal/scope 모호성, external benchmark, option comparison, 구조 분해, public/shared boundary 리스크가 있을 때 conditional로 추가한다.
- AI/agent workflow planning은 `web-researcher`를 official vendor docs 우선 조사 용도로 사용한다.

## 자동 리뷰 트리거

트리거 임계값은 `workflow.toml [review_triggers]`에서 관리한다.

- reviewer는 지적 전용이 아니라 quality preflight lane 판정과 focused gate를 담당한다.
- quality preflight에서 TS/JS/React 기존 코드는 `explorer`를 기본으로 붙인다.
- 구조 냄새가 있으면 `complexity-analyst`, `structure-planner`, `test-engineer`를 추가한다.
- `architecture-reviewer`는 public/shared boundary 예상 시에만 붙인다.
- `code-quality-reviewer`는 아래 중 하나라도 만족할 때 실행한다.
  - 변경 파일 수가 임계값 이상
  - 테스트가 추가되거나 변경됨
  - 에러 처리/동시성/보안 민감 로직이 변경됨
  - 사용자가 명시적으로 리뷰를 요청함
- `architecture-reviewer`는 아래 중 하나라도 만족하면 실행한다.
  - 변경 파일 수가 임계값 이상
  - 모듈/패키지 경계 변경 수가 임계값 이상
  - public surface 변경 (export, entrypoint, 핵심 설정)
- `structure-planner`는 아래 조건에서 quality preflight escalation 또는 `design-task` 내부 fan-out으로 실행한다.
  - `structure preflight`에서 `split-first` trigger가 켜진 경우
  - 예상 diff 또는 변경 파일 수가 임계값 이상인 경우
  - 대상 기존 코드 파일이 soft limit(`workflow.toml [structure_policy.role_limits]`)에 근접하거나 초과해 분해 설계가 필요한 경우
- `structure-gatekeeper`는 비trivial code diff 이후 실행한다. frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`)도 함께 커버한다.
  - FAIL 판정은 공통/React 구조 관점에서 P1로 취급한다.
  - 이미 soft limit를 넘긴 파일에 additive diff를 더하면 strong mode에서 FAIL이다.
- `type-specialist`는 shared/public types, generics, public contract 변경 시 실행한다.
- `test-engineer`는 회귀 리스크가 크거나 테스트 커버리지 공백이 있을 때 실행한다.

## 서브 에이전트 응답 가이드라인

- quality preflight/reviewer helper는 `품질판정: keep-local | orchestrated-task`를 포함한다.
- `orchestrated-task`일 때는 `work_type`와 핵심 `impact_flags`를 함께 적는다.
- 필수 항목은 `핵심결론`, `근거`다.
- 선택 항목은 `리스크`, `권장 다음 행동`, `추가 확인 필요`다.
- 원문 출력이 필요하면 최소 발췌만 포함하고 소스 경로를 명시한다.
