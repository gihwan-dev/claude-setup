<!-- AUTO-GENERATED from INSTRUCTIONS.md. Do not edit directly. -->
<!-- Run: ./scripts/sync-instructions.sh -->

# 멀티 에이전트 오케스트레이션 정책

## 핵심 목표

메인 스레드는 전략과 의사결정에 집중한다.
실행 작업은 필요한 경우에만 위임하고, 간결한 요약만 반환받는다.

## 오케스트레이션 기본 규칙

- 작업 복잡도와 영향 범위를 먼저 평가한다.
- 기본은 메인 스레드 단일 실행(single-agent)과 직접 수정이다.
- 병렬 read-only 작업은 분명한 이점이 있을 때만 사용한다.
- delegated lane의 code diff는 단일 writer만 허용하고 writable projection은 `worker`만 사용한다.
- 서브 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 하드 라우팅 규칙 (필수)

### Triage first

- 어떤 에이전트도 spawn하기 전에 먼저 quality preflight를 통해 승격 여부와 lane을 결정한다.

### Quality preflight

- 기존 코드 수정/리뷰/`계속해`/`다음 단계`/버그 수정/기능 추가 요청에는 lane 판정 전에 quality preflight를 먼저 수행한다.
- 예외는 fast lane 조건을 모두 만족하는 명백한 1파일 소규모 수정이다.
- quality preflight 결과는 `keep-local` / `promote-refactor` / `promote-architecture` 셋 중 하나로 기록한다.
- 아래 중 하나라도 해당하면 자동 승격한다.
  - 2개 이상 파일 변경이 예상되거나 delegated 기준에 해당함
  - CC > 10 또는 중첩 > 2
  - 대상 기존 코드 파일이 soft limit에 근접하거나 초과했고 책임이 혼재함
  - dead code, unused export/helper, 테스트 중복 정리가 함께 보임
  - 컴포넌트/훅/스토리지/정책 계산이 한 파일이나 흐름에 혼재함
- 구현 요청은 `keep-local`이면 기존 fast/deep-solo/delegated lane 규칙으로 처리하고 `design-task`/`implement-task` long-running path는 시작하지 않는다.
- `promote-refactor`면 `design-task` 성격의 리팩터링 계획을 먼저 만든 뒤 `implement-task` slice로 진행한다.
- `promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향을 먼저 고정한 뒤 slice를 설계한다.
- 기존 코드의 long-running `design-task`/`implement-task` 경로는 `promote-refactor` 또는 `promote-architecture`일 때만 시작한다.
- 리뷰 요청은 findings-first를 유지한다. `promote-refactor` 판정이면 같은 턴에 구조 개선 계획 요약을 함께 제공한다.
- TS/JS/React 기존 코드는 quality preflight에서 `explorer`를 기본으로 사용한다.
- 구조 냄새가 보이면 `complexity-analyst`, `structure-planner`, `test-engineer`를 추가하고, public/shared boundary 변경이 예상될 때만 `architecture-reviewer`를 붙인다.

### Fast lane: direct edit in main thread

- 아래 조건을 모두 만족하면 메인 스레드가 직접 수정한다.
  - 변경이 1개 파일 범위로 제한됨
  - 변경량이 소규모(diff가 작음)
  - public API/schema/config/migration/shared type/cross-module boundary 변경이 없음
  - 원인과 대상 파일이 명확함
  - 검증을 1개 집중 체크로 마무리할 수 있음

### Deep solo lane: direct non-trivial edit in main thread

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

### Single-writer rule (delegated lane only)

- delegated lane의 code diff는 정확히 하나의 `worker`만 적용한다.
- 같은 실행 단위에서 두 번째 writer를 투입하지 않는다.
- writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.

## 필수 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 메인 스레드에서 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때만 `explorer`를 사용한다.
2. 메인 스레드에서 의사결정을 확정한다.
3. 정확히 하나의 `worker`가 필요한 code diff를 적용한다.
4. 검증 출력이 noisy/multi-step일 때만 `verification-worker`를 사용한다.
5. 메인 스레드가 결과를 통합해 최종 응답한다.

### Long-running `implement-task` path

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- `implement-task` long-running path는 single-writer delegated flow를 유지한다.
- writable projection은 `worker`만 허용하고 slice마다 정확히 한 명만 code diff를 적용한다.
- 각 slice는 `worker edit -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision` 순서를 따른다.
- helper fan-out은 탐색/리뷰/검증 로그 해석이 필요할 때만 read-only로 사용한다.
- phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.
- noisy/multi-step validation log는 `verification-worker`가 메인 검증 로그를 해석한다.
- focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 해당 slice를 실패로 기록하고 다음 slice로 진행하지 않는다.
- slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.
- `wait timeout`은 stalled와 동일하지 않다.
- `liveness gate`와 `completion gate`를 분리한다.
- close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.
- `explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.
- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.
- advisory reviewer 미응답은 slice 실패로 처리하지 않고 background/advisory로 전환한다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 승격하고, 그 외에는 advisory로 처리한다.
- core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.
- interrupt/close 요청 시 helper는 새 작업 시작을 중지하고 `final` 또는 최소 `checkpoint/preliminary`를 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 메인 스레드는 helper 요약을 통합해 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.
- planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- `monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection은 만들지 않는다.
- helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)는 runtime helper로 보장되어야 하며 각 `agent.toml`의 `[orchestration]`을 SSOT로 유지한다.

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| main-thread | 쓰기 가능 | 전략, focused validation, 상태 통합/기록 |
| worker | 읽기/쓰기 | delegated lane과 `implement-task` slice의 유일한 code diff writer |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | quality preflight 승격 판정과 구조/검증 게이트 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## 역할-실행 매핑

| 작업 성격 | 워크플로우 역할 | 보조 수단 |
|-----------|----------------|-----------|
| 코드 탐색/분석 | explorer | — |
| React UI 구현 | main-thread | 관련 skill/레퍼런스만 사용 |
| 테스트 작성 | main-thread | 관련 skill/레퍼런스만 사용 |
| 코드 품질 리뷰 | reviewer | code-reviewer |
| 아키텍처 리뷰 | reviewer | architecture-reviewer |
| 리팩토링 실행 | main-thread | 관련 skill/레퍼런스만 사용 |
| TypeScript 타입 설계 | main-thread | 관련 skill/레퍼런스만 사용 |
| 인터페이스 품질 점검 | reviewer | interface-inspector |
| 정량 복잡도 분석 | reviewer | complexity-analyst |
| 공통 모듈 구조 분해 계획(구현 전) | reviewer | structure-planner |
| 공통 구조 게이트 리뷰(구현 후) | reviewer | module-structure-gatekeeper |
| React 구조 게이트 리뷰(구현 후) | reviewer | frontend-structure-gatekeeper |
| 장기 작업 설계/실행 | main-thread | `design-task`, `implement-task` |
| Storybook/디자인 검증 | main-thread | 관련 skill/레퍼런스만 사용 |
| 프롬프트 최적화 | main-thread | 관련 skill/레퍼런스만 사용 |
| 검증/결과 분석 | verifier | — |

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
  - 도메인과 무관하게 아래 조건 중 하나면 실행한다.
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

서브 에이전트는 간결하고 의사결정 가능한 요약을 우선한다.
quality preflight/reviewer helper는 `품질판정: keep-local | promote-refactor | promote-architecture`를 포함한다.

**필수 항목:**
1. 핵심결론
2. 근거 (`file:line` 또는 `error-id`)

**선택 항목 (관련 시):**
3. 리스크
4. 권장 다음 행동
5. 추가 확인 필요 (불확실성/차단 요인)

원문 출력이 필요하면 최소 발췌만 포함하고 소스 경로를 명시한다.

## 에이전트 정의 소스

에이전트의 단일 진실원은 `agent-registry/<agent-id>/agent.toml` + `instructions.md`다.
`agents/*.md`는 수기 파일이 아니라 registry에서 생성되는 projection이다.
Codex 런타임용 프로파일은 registry에서 `dist/codex/agents/*.toml`과 `dist/codex/config.managed-agents.toml`로 생성한다.

## 언어 및 스타일

- 설명은 기본적으로 한국어를 사용한다.
- 코드 식별자, 명령어, 로그는 원어를 유지한다.
