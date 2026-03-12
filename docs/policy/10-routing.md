## 하드 라우팅 규칙

### Triage first

- 어떤 에이전트도 spawn하기 전에 먼저 quality preflight를 통해 direct lane 유지 여부와 long-running orchestration 진입 여부를 결정한다.

### Quality preflight

- 기존 코드 수정/리뷰/`계속해`/`다음 단계`/버그 수정/기능 추가 요청에는 lane 판정 전에 quality preflight를 먼저 수행한다.
- 기존 TS/JS/React 코드 파일을 건드릴 때는 quality preflight 안에서 `structure preflight`를 fast lane 판정보다 먼저 수행한다.
- `structure preflight`는 대상 파일 역할 분류, 예상 post-change LOC, `split-first` 필요 여부를 고정한다.
- 예외는 fast lane 조건을 모두 만족하는 명백한 1파일 소규모 수정이다.
- quality preflight 결과는 `keep-local` 또는 `orchestrated-task`로 기록한다.
- 아래 중 하나라도 해당하면 `orchestrated-task`로 승격한다.
  - 2개 이상 파일 변경이 예상되거나 delegated 기준에 해당함
  - CC > 10 또는 중첩 > 2
  - 대상 기존 코드 파일이 soft limit에 근접하거나 초과했고 책임이 혼재함
  - `structure preflight`에서 `split-first` trigger가 켜짐
  - dead code, unused export/helper, 테스트 중복 정리가 함께 보임
  - 컴포넌트/훅/스토리지/정책 계산이 한 파일이나 흐름에 혼재함
- 구현 요청은 `keep-local`이면 기존 fast/deep-solo/delegated lane 규칙으로 처리하고 `design-task`/`implement-task` long-running path는 시작하지 않는다.
- `orchestrated-task`면 `design-task`가 `work_type + impact_flags + delivery_strategy`를 결정하고 task bundle을 만든 뒤 `implement-task` slice로 진행한다.
- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `delivery_strategy=ui-first`를 사용한다.
- AI/agent workflow planning이면 `web-researcher` 또는 메인 스레드 직접 웹 조사로 official vendor docs를 우선 확인한다.
- 구조/공개 경계 리스크가 높으면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향을 먼저 고정한다.
- 기존 코드의 long-running `design-task`/`implement-task` 경로는 refactor/architecture에 한정하지 않고 non-trivial task 전반(`feature`, `bugfix`, `refactor`, `migration`, `prototype`, `ops`)에 사용한다.
- 리뷰 요청은 findings-first를 유지한다. `orchestrated-task` 판정이면 같은 턴에 구조 개선 또는 bundle 설계 방향을 함께 제공한다.
- TS/JS/React 기존 코드는 quality preflight에서 `explorer`를 기본으로 사용한다.
- 구조 냄새가 보이면 `complexity-analyst`, `structure-planner`, `test-engineer`를 추가하고, public/shared boundary 변경이 예상될 때만 `architecture-reviewer`를 붙인다.

### Fast lane

- 아래 조건을 모두 만족하면 메인 스레드가 직접 수정한다.
  - `structure preflight`가 끝났고 `split-first` trigger가 꺼져 있음
  - 변경이 1개 파일 범위로 제한됨
  - 변경량이 소규모(diff가 작음)
  - public API/schema/config/migration/shared type/cross-module boundary 변경이 없음
  - 원인과 대상 파일이 명확함
  - 검증을 1개 집중 체크로 마무리할 수 있음

### Deep solo lane

- 변경이 크더라도 아래 조건이면 메인 스레드가 계속 직접 구현할 수 있다.
  - 메인 스레드가 이미 충분한 맥락을 확보함
  - 변경이 동일 모듈/작업 흐름 안에서 닫힘
  - 서브 에이전트 병렬 조율 이점이 낮음
- Deep solo lane에서도 핵심 시나리오 검증과 잔여 리스크 보고는 필수다.

### Delegated team lane

- 아래 중 하나라도 해당하면 위임을 사용한다.
  - 2개 이상 파일 변경이 예상됨
  - 탐색/증거 수집이 필요함
  - 원인 또는 소유 영역이 불명확함
  - 공유 경계 또는 public surface 변경이 포함됨
  - 검증 로그가 noisy하거나 multi-step임

### Single-writer rule

- delegated lane의 code diff는 정확히 하나의 `worker`만 적용한다.
- 같은 실행 단위에서 두 번째 writer를 투입하지 않는다.
- writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.

### Exit documentation review

- 모든 lane은 종료 전에 메인 스레드가 실질 영향이 있는 문서만 다시 탐색하고 검토한다.
- 기본 대상 예시는 `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs다.
- 문서 영향 대상이 불명확할 때만 read-only helper로 후보를 좁힌다.
- `docs/policy`, `skills`, `agent-registry` 같은 SSOT가 바뀌면 관련 generated projection sync와 대응 `--check`를 통과시킨 뒤 종료한다.
