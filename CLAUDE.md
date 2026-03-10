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
- 위임된 수정 작업은 단일 작성자(single-writer)만 허용한다.
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
- Do not spawn worker for fast-lane tasks.

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

- 기본값: delegated lane 한 실행 단위(run)에서 정확히 하나의 `worker`가 code diff를 적용한다.
- 동일 작업에서 writer 에이전트를 둘 이상 사용하지 않는다.

## 필수 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 메인 스레드에서 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때만 `explorer`를 사용한다.
2. 메인 스레드에서 의사결정을 확정한다.
3. 정확히 하나의 `worker`를 spawn해서 변경을 적용한다.
4. 검증 출력이 noisy/multi-step일 때만 `verification-worker`를 사용한다.
5. 메인 스레드가 결과를 통합해 최종 응답한다.

### Exception: `project-planner` + `implement-task`

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- `project-planner`가 `implement-task`를 실행할 때는 fast lane/deep solo를 적용하지 않고 항상 delegated team lane으로 실행한다.
- 오케스트레이터는 strategy-only 역할로 제한한다. 직접 코드 수정이나 raw validation log 해석을 수행하지 않는다. 단, non-mutating focused validation 실행은 허용한다.
- single-writer 적용 단위는 run이 아니라 slice다. 각 slice의 code diff ownership은 fresh `worker` 1명이 담당한다.
- `끝까지` 모드에서 여러 slice에 서로 다른 fresh `worker`가 참여해도 slice당 single-writer를 만족하면 규칙 위반이 아니다.
- 각 slice는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 순서를 따른다.
- slice가 refactor/test/type-contract 성격을 가질 수 있어도 code diff를 적용하는 protocol-level writer는 항상 `worker`다.
- phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.
- noisy/multi-step validation log는 `verification-worker`가 메인 검증 로그를 해석한다.
- focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 해당 slice를 실패로 기록하고 다음 slice로 진행하지 않는다.
- `fork_context` 기본값은 `false`다. 축약 불가능한 컨텍스트 의존일 때만 `true`를 허용하고 이유를 `STATUS.md`에 기록한다.
- slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.
- 멀티에이전트 생명주기 경계는 `inactivity window`, `blocking deadline`, `drain grace` 3개로 고정한다. raw second(예: 90초/60초)는 정책 문구로 고정하지 않는다.
- stall 판정은 `communication liveness`와 `execution liveness`가 모두 끊긴 경우에만 허용한다.
- close 절차는 `liveness 확인 -> interrupt로 final/checkpoint flush 요청 -> drain grace 대기 -> 결과 ACK -> close_agent` 순서를 따른다.
- `wait timeout = 즉시 실패/즉시 close` 규칙을 금지한다.
- `worker` 실패는 `상태: blocked`이거나 dual-signal inactivity 이후 drain grace 안에 `final/checkpoint`가 없을 때만 기록한다.
- advisory reviewer 미응답은 slice 실패로 처리하지 않고 background/advisory로 전환한다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 승격하고, 그 외에는 advisory로 처리한다.
- writer handoff brief에는 `blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`를 포함하고 raw second는 적지 않는다.
- core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.
- interrupt/close 요청 시 helper는 새 작업 시작을 중지하고 `final` 또는 최소 `checkpoint/preliminary`를 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.
- 같은 slice에 두 번째 writer를 투입하지 않는다.
- partial diff가 남으면 오케스트레이터는 read-only로 확인만 하고 `STATUS.md`에 기록한 뒤 재설계한다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다. `STATUS.md` 갱신은 code diff ownership / single-writer 집계 대상에서 제외한다.
- 오케스트레이터는 요약 결과만 받아 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.
- planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`)는 runtime helper로 보장되어야 하며 각 `agent.toml`의 `[orchestration]`을 SSOT로 유지한다.

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| orchestrator | 전략만 | 계획, 라우팅, 최종 의사결정 |
| implementer | 읽기/쓰기 | delegated lane의 유일한 코드 변경 수행자 |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | quality preflight 승격 판정과 구조/검증 게이트 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## 역할-에이전트 매핑

| 작업 성격 | 워크플로우 역할 | 도메인 에이전트 |
|-----------|----------------|----------------|
| 코드 탐색/분석 | explorer | — |
| React UI 구현 | implementer | frontend-developer |
| 테스트 작성 | implementer | qa-engineer |
| 코드 품질 리뷰 | reviewer | code-reviewer |
| 아키텍처 리뷰 | reviewer | architecture-reviewer |
| 리팩토링 실행 | implementer | refactoring-expert |
| TypeScript 타입 설계 | implementer | typescript-pro |
| 인터페이스 품질 점검 | reviewer | interface-inspector |
| 정량 복잡도 분석 | reviewer | complexity-analyst |
| 공통 모듈 구조 분해 계획(구현 전) | reviewer | structure-planner |
| 공통 구조 게이트 리뷰(구현 후) | reviewer | module-structure-gatekeeper |
| React 구조 게이트 리뷰(구현 후) | reviewer | frontend-structure-gatekeeper |
| 장기 작업 설계/실행 오케스트레이션 | orchestrator | project-planner |
| Storybook/디자인 검증 | implementer | storybook-specialist |
| 프롬프트 최적화 | implementer | prompt-engineer |
| 검증/결과 분석 | verifier | — |

## Internal Planning Roles

- `web-researcher`, `solution-analyst`, `product-planner`, `structure-planner`, `ux-journey-critic`, `delivery-risk-planner`, `prompt-systems-designer`
- 위 role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.

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
