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

- 어떤 에이전트도 spawn하기 전에 먼저 lane을 결정한다.

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

- `project-planner`가 `implement-task`를 실행할 때는 fast lane/deep solo를 적용하지 않고 항상 delegated team lane으로 실행한다.
- 오케스트레이터는 strategy-only 역할로 제한한다. 직접 코드 수정이나 raw validation log 해석을 수행하지 않는다.
- single-writer 적용 단위는 run이 아니라 slice다. 각 slice의 code diff는 fresh `worker` 1명이 담당한다.
- `끝까지` 모드에서 여러 slice에 서로 다른 fresh `worker`가 참여해도 slice당 single-writer를 만족하면 규칙 위반이 아니다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다. `STATUS.md` 갱신은 code diff ownership / single-writer 집계 대상에서 제외한다.
- 검증 실행은 writer가 담당하고, noisy/multi-step 로그 해석만 `verification-worker`에 위임한다.
- 오케스트레이터는 요약 결과만 받아 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| orchestrator | 전략만 | 계획, 라우팅, 최종 의사결정 |
| implementer | 읽기/쓰기 | delegated lane의 유일한 코드 변경 수행자 |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | 코드 품질, 아키텍처 리뷰 |
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
| 장기 작업 설계/실행 오케스트레이션 | orchestrator | project-planner |
| Storybook/디자인 검증 | implementer | storybook-specialist |
| 프롬프트 최적화 | implementer | prompt-engineer |
| 외부 리서치/경쟁사 벤치마킹 | explorer | web-researcher |
| 솔루션 옵션 비교/트레이드오프 분석 | reviewer | solution-analyst |
| 요구사항/성공 기준 구조화 | orchestrator | product-planner |
| UX 여정/마찰/엣지 상태 점검 | reviewer | ux-journey-critic |
| 전달/롤아웃 리스크 설계 | reviewer | delivery-risk-planner |
| 프롬프트 시스템 계약/평가 설계 | reviewer | prompt-systems-designer |
| 검증/결과 분석 | verifier | — |

## 자동 리뷰 트리거

- `code-quality-reviewer`는 아래 중 하나라도 만족할 때만 실행한다.
  - 변경 파일이 3개 이상
  - 테스트가 추가되거나 변경됨
  - 에러 처리/동시성/보안 민감 로직이 변경됨
  - 사용자가 명시적으로 리뷰를 요청함
- `architecture-reviewer`는 아래 중 하나라도 만족하면 실행한다.
  - 변경 파일 7개 이상
  - 모듈/패키지 경계 2개 이상 변경
  - public surface 변경 (export, entrypoint, 핵심 설정)
- `type-specialist`는 shared/public types, generics, public contract 변경 시 실행한다.
- `test-engineer`는 회귀 리스크가 크거나 테스트 커버리지 공백이 있을 때 실행한다.

## 서브 에이전트 응답 가이드라인

서브 에이전트는 간결하고 의사결정 가능한 요약을 우선한다.

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
