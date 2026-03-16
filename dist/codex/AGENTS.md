<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Installed to ~/.codex/AGENTS.md as global Codex policy. -->

# Multi-Agent Orchestration Policy

이 정책은 모든 프로젝트에 적용되는 Codex global orchestration 규칙이다.
프로젝트별 추가 규칙은 해당 프로젝트의 `AGENTS.md`를 참조한다.

## 핵심 목표

메인 스레드는 전략과 의사결정에 집중한다.
실행 작업은 필요한 경우에만 위임하고, 간결한 요약만 반환받는다.

## 오케스트레이션 기본 규칙

- 작업 복잡도와 영향 범위를 먼저 평가한다.
- 기본은 메인 스레드 단일 실행(single-agent)과 직접 수정이다.
- 병렬 read-only 작업은 분명한 이점이 있을 때만 사용한다.
- delegated lane의 code diff ownership을 별도 writer에 고정하지 않는다.
- 서브 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 역할-실행 매핑

| 작업 성격 | 워크플로우 역할 | 보조 수단 |
|-----------|----------------|-----------|
| 코드 탐색/분석 | explorer | — |
| 브라우저 탐색/재현 | explorer | browser-explorer |
| React UI 구현 | main-thread | 관련 skill/레퍼런스만 사용 |
| 테스트 작성 | main-thread | 관련 skill/레퍼런스만 사용 |
| 코드 품질 리뷰 | reviewer | code-reviewer |
| 아키텍처 리뷰 | reviewer | architecture-reviewer |
| 리팩터링 실행 | main-thread | 관련 skill/레퍼런스만 사용 |
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

- `design-task`는 non-trivial long-running 작업에서 task bundle(`task.yaml`, `README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, `STATUS.md`)을 설계하고 `delivery_strategy`를 확정한다.
- UI 영향 task는 `delivery_strategy=ui-first`를 기본값으로 사용하고 `UI -> local state/mock -> real API/integration` 순서로 slice를 만든다.
- `implement-task`는 새 bundle을 우선 읽고, 기존 `PLAN.md`/`STATUS.md` task는 fallback compatibility로만 다룬다.

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
  - CC 또는 중첩 깊이가 임계값 초과 (`workflow.toml [quality_preflight]` 참조)
  - 대상 기존 코드 파일이 soft limit에 근접하거나 초과했고 책임이 혼재함
  - `structure preflight`에서 `split-first` trigger가 켜짐
  - dead code, unused export/helper, 테스트 중복 정리가 함께 보임
  - 컴포넌트/훅/스토리지/정책 계산이 한 파일이나 흐름에 혼재함
- 구현 요청은 `keep-local`이면 기존 fast/deep-solo/delegated lane 규칙으로 처리하고 `design-task`/`implement-task` long-running path는 시작하지 않는다.
- `orchestrated-task`면 `design-task`가 `work_type + impact_flags + delivery_strategy`를 결정하고 task bundle을 만든 뒤 `implement-task` slice로 진행한다.
- delegated/long-running hybrid mode default는 `small slices + run-to-boundary`다.
- broad `setup`/`skeleton`/`wrapper`/`docs` handoff이거나 slice budget(`workflow.toml [slice_budget]` 참조)을 넘는 PREP-0 스타일 handoff는 실행 전에 `split/replan before execution`으로 되돌린다.
- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `delivery_strategy=ui-first`를 사용한다.
- AI/agent workflow planning이면 `web-researcher` 또는 메인 스레드 직접 웹 조사로 official vendor docs를 우선 확인한다.
- 구조/공개 경계 리스크가 높으면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향을 먼저 고정한다.
- 기존 코드의 long-running `design-task`/`implement-task` 경로는 refactor/architecture에 한정하지 않고 non-trivial task 전반(`feature`, `bugfix`, `refactor`, `migration`, `prototype`, `ops`)에 사용한다.
- 리뷰 요청은 findings-first를 유지한다. `orchestrated-task` 판정이면 같은 턴에 구조 개선 또는 bundle 설계 방향을 함께 제공한다.
- TS/JS/React 기존 코드는 quality preflight에서 `explorer`를 기본으로 사용한다.
- live browser reproduction, DOM/visual QA, screenshot evidence가 필요한 task는 메인 스레드 대신 `browser-explorer`를 선택적 fan-out으로 사용한다. `explorer`는 레포 탐색용으로 유지한다.
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

### Delegated execution guardrails

- delegated lane의 code diff ownership을 별도 writer에 고정하지 않는다.
- `wait timed_out` 시 허용 경로는 `longer wait -> optional queued status probe -> background or natural completion`이다. non-interrupt status ping은 queued-only semantics다.
- Immediate status check requires explicit cancel path.

### Exit documentation review

- 모든 lane은 종료 전에 메인 스레드가 실질 영향이 있는 문서만 다시 탐색하고 검토한다.
- 기본 대상 예시는 `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs다.
- 문서 영향 대상이 불명확할 때만 read-only helper로 후보를 좁힌다.

## Structure-First Authoring

### Structure preflight

- 기존 TS/JS/React 코드 파일을 수정할 때는 fast lane 여부를 보기 전에 `structure preflight`를 먼저 수행한다.
- `structure preflight`는 최소 아래 세 가지를 고정한다.
  - 대상 파일 역할 분류 (`component`, `view`, `hook`, `provider`, `view-model`, `composable`, `middleware`, `service`, `use-case`, `repository`, `controller`, `util`, `adapter`)
  - 예상 post-change LOC
  - `split-first` 필요 여부
- `split-first`가 켜지면 기존 파일에 그대로 append하지 않고, 같은 slice 안에서 분해하거나 범위 초과 시 `blocked + exact split proposal`로 되돌린다.

### Split-First Triggers

- 아래 중 하나라도 해당하면 `split-first`다.
  - 대상 파일이 soft limit에 근접하거나 이미 초과했다.
  - 이번 변경이 새 책임을 추가한다.
  - util/service/use-case/repository 성격 코드를 component/view 파일에 붙이려 한다.
  - 반복 stateful 또는 branch-heavy 로직을 기존 파일에 더 얹으려 한다.

### Strong Mode

- soft limit 근접/초과 파일에는 append를 허용하지 않는다.
- 이미 soft limit를 넘긴 파일에 additive diff를 더하면 `FAIL`이다.
- hard limit 초과와 책임 혼합은 항상 `FAIL`이다.
- 기존 레거시 과대 파일을 건드리지 않는 경우에만 advisory를 허용한다.

### Scope Discipline

- 루트 메모리는 짧게 유지하고, 세부 구조 규칙은 specialized agent/skill contract와 machine-readable policy로 관리한다.
- user-facing long-running surface는 계속 `design-task`, `implement-task`만 유지한다.
- 새 task의 source of truth는 `task.yaml` bundle이며, `PLAN.md`는 legacy fallback compatibility로만 유지한다.

## 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 실질 영향 문서만 재탐색/검토하고 필요한 sync/check를 마무리한다.
5. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때 `explorer`를 사용한다.
2. live browser reproduction, visual evidence 확인이 필요할 때 `browser-explorer`를 사용한다. handoff에 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
3. 메인 스레드에서 의사결정을 확정한다.
4. 현재 slice의 code/doc diff를 적용한다.
5. `small slices + run-to-boundary`를 기본으로 사용한다. slice budget(`workflow.toml [slice_budget]` 참조)을 넘는 handoff는 split/replan으로 되돌린다.
6. 문서 영향 여부를 판정하고 문서 diff는 focused validation 전에 구현 단계에서 반영한다.
7. 검증 출력이 noisy/multi-step일 때 `verification-worker`를 사용한다.
8. 실질 영향 문서 재검토와 sync/check를 마무리한다.
9. 결과를 통합해 최종 응답한다.

### Long-running path 개요

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- 여러 active task 폴더 공존은 정상 경로다.
- 상세 워크플로우는 아래 문서를 참조한다.
  - `21-design-task.md`: design-task 워크플로우와 delivery strategy
  - `22-implement-task.md`: implement-task 실행, 검증, sync 규칙
  - `23-helper-protocol.md`: helper agent close/timeout 계약

## design-task 워크플로우

### 기본 흐름

- `design-task`는 `task.yaml` 중심 task bundle을 만든다.
- continuity gate를 통과한 경우에만 기존 task를 재사용한다.
- greenfield/new-project는 post-design bootstrap skill(`bootstrap-project-rules`)로 repo baseline을 만들 수 있다.
- `work_type + impact_flags + delivery_strategy`를 결정한다.
- 각 slice에 `split decision`을 기록하고 target-file append 금지 trigger를 명시한다.

### delivery_strategy

- `task.yaml`의 `delivery_strategy`는 `standard` 또는 `ui-first`를 사용한다 (`workflow.toml [task_documents]` 참조).
- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나이고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `ui-first`를 사용한다.
- `ui-first`일 때 `design-task`는 내부 advisory skill `reference-pack`을 자동 실행해 `DESIGN_REFERENCES/`를 채운 뒤, `figma-less-ui-design`으로 `UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md`를 생성한다.
- 기존 design system, shipped UI, brand guide, Figma가 있으면 `reuse + delta`를 기록한다.

### UX 문서 섹션 순서

`UX_SPEC.md` (UI Planning Packet): `Goal/Audience/Platform`, `30-Second Understanding Checklist`, `Visual Direction + Anti-goals`, `Reference Pack (adopt/avoid)`, `Glossary + Object Model`, `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`, `Implementation Prompt/Handoff`

`UX_BEHAVIOR_ACCESSIBILITY.md`: `Interaction Model`, `Keyboard + Focus Contract`, `Accessibility Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, `Microcopy + Information Expression Rules`, `Task-based Approval Criteria`

### planning role fan-out

- UI 영향 planning은 `ux-journey-critic`를 mandatory 기본값으로 둔다.
- 조건부 추가: scope 모호 → `product-planner`, external benchmark → `web-researcher`, option comparison → `solution-analyst`, 구조 분해 → `structure-planner`, public/shared boundary 리스크 → `architecture-reviewer`
- AI/agent workflow planning은 `web-researcher`로 official vendor docs를 우선 조사한다.

### task bundle

- core docs: `task.yaml`, `README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, `STATUS.md`
- `task.yaml`은 machine entry point, `README.md`는 사람용 landing 문서다.
- post-design bootstrap 적용 시 repo baseline source는 `docs/ai/ENGINEERING_RULES.md`이고, task bundle에 optional `IMPLEMENTATION_CONTRACT.md`가 추가될 수 있다.
- 새 task는 `task.yaml` bundle을 사용한다. legacy task만 `PLAN.md`를 유지한다.
- `work_type + impact_flags`로 필수/선택 문서를 고르고 `required_docs`에 기록한다.

### SPEC_VALIDATION

- 모든 task에 `SPEC_VALIDATION.md`를 생성한다.
- gate 값은 `blocking` 또는 `advisory`를 사용한다.
- `bundle_blocking_validation_flags`(`workflow.toml` 참조) 중 하나가 있거나 설계 문서가 임계값 이상이면 `blocking`을 사용한다 (`workflow.toml [review_triggers]` 참조).
- 섹션 순서: `Requirement coverage`, `UX/state gaps`, `Architecture/operability risks`, `Slice dependency risks`, `Blocking issues`, `Proceed verdict`
- greenfield/new-project에서 repo implementation rules가 아직 없으면 `Blocking issues`에 `$bootstrap-project-rules` 실행 요구를 남긴다.

### ui-first execution plan

- `EXECUTION_PLAN.md`는 `SLICE-1=static/visual UI`, `SLICE-2=local state/mock`, `SLICE-3+=real API/integration` 순서를 유지한다.
- `SLICE-1`/`SLICE-2`에는 static/mock UI만 포함한다.
- `implement-task`에서 `SLICE-1`은 `UX_SPEC.md`의 checklist/layout/token/screen-flow와 `UX_BEHAVIOR_ACCESSIBILITY.md`의 interaction/a11y/microcopy를 읽는다.
- `SLICE-2`는 keyboard/focus, live semantics, state matrix/fixture, degradation, task-based approval criteria를 읽는다.
- `SLICE-1` 승인과 `SLICE-2` 상태 모델 확정 후 다음 slice로 진행한다.

## implement-task 실행

### 진입 조건

- 새 task에서 `task.yaml + EXECUTION_PLAN.md + STATUS.md`를 우선 읽는다.
- `blocking` validation을 해소한 뒤 구현을 시작한다.
- `source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`를 함께 읽는다.
- `task.yaml.delivery_strategy`를 구현 계약으로 읽고, `ui-first`면 early UI slice에는 static/mock만 포함한다.

### slice 생명주기

- 각 slice는 `slice implementation(구현 + 필요한 문서/source-of-truth 반영) -> main focused validation -> commit -> STATUS update -> next slice decision` 순서를 따른다.
- 문서 diff는 구현 단계에서 focused validation 전에 함께 반영한다.
- 문서 영향 판정은 메인 스레드 기본 책임이다.
- 문서 diff도 slice budget에 포함한다. budget을 넘기면 replan한다.

### 실행 guardrails

- path 미지정 시 자동 선택은 후보가 1개일 때만 허용한다. 2개 이상이면 사용자 확인을 기다린다.
- pre-edit 상태 보고는 1회 structure preflight로 마친다.
- slice budget(`workflow.toml [slice_budget]` 참조)을 넘는 handoff는 `split/replan before execution`으로 되돌린다.
- soft limit를 넘긴 파일은 additive diff 대신 split을 사용한다 (strong mode).
- 공통 리팩터링, 여러 화면 치환, 테스트 전수 갱신, 정적 스캔은 별도 slice로 분리한다.
- full-history/forked-context는 thread-local reasoning 또는 uncommitted local state lineage가 필요할 때 사용한다.

### helper 활용

- helper fan-out은 탐색/리뷰/검증 로그 해석이 필요할 때 read-only로 사용한다.
- browser-explorer는 live browser reproduction, DOM/visual QA, screenshot evidence가 필요할 때 사용한다. handoff에 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본으로 두고, advisory helper fan-out은 slice 의사결정을 바꿀 때만 사용한다.

### 검증

- phase 2 기본 검증: `타깃 검증 1개 + 저비용 체크 1개`. shared/public boundary 변경일 때만 full-repo validation을 사용한다.
- noisy/multi-step validation log는 `verification-worker`가 해석한다.
- focused validation 실패 시 해당 slice를 커밋하지 않고 원인을 해결한다.
- `STATUS.md` 구현 요약에 문서 영향 판단을 남기고, `Verification results`에 sync/check 명령과 pass/fail을 남긴다.

### 커밋과 sync

- hook 실패로 커밋이 막히면 동일 메시지로 `git commit --no-verify`를 1회 재시도한다.
- 재시도까지 실패하면 해당 slice를 실패로 기록하고 원인을 해결한다.

### 종료

- 종료 전 메인 스레드는 실질 영향 문서만 다시 탐색/검토한다.
- 기본 대상: `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs
- 문서 대상이 불명확할 때만 read-only helper를 사용한다.

## Helper agent 계약

### timeout과 close 기본 원칙

- `wait timeout`과 stalled는 다른 상태다. `liveness gate`와 `completion gate`를 분리한다.
- non-interrupt status ping은 queued-only semantics를 따른다.
- 상세 값은 `workflow.toml [helper_close]`를 참조한다.

### timeout 경로

- `wait timed_out` 시: `longer wait -> optional queued status probe -> background or natural completion` 경로를 따른다.
- `non-cancel observe path`: `wait -> inspect/status ping(interrupt=false) -> observe/drain -> background or natural completion`
- Immediate status check requires explicit cancel path.

### cancel 경로

- `explicit cancel path`: `wait -> inspect/status ping -> interrupt -> drain grace -> close 판단`
- non-cancel 경로에서는 synthetic interrupt를 보내지 않는다.
- `explicit cancel`만 종료 근거로 사용한다. `result가 더 이상 필요 없음`은 종료 근거가 아니다.
- `wait timed_out → status running → no result → close`는 유효하지 않은 시퀀스다.

### advisory helper 규칙

- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않고, background/advisory로 유지한다.
- advisory helper 미응답은 slice 실패가 아니라 background/advisory로 전환한다.
- 늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.
- `verification-worker`는 commit sign-off가 필요할 때만 semi-blocking으로 승격하고, 그 외에는 advisory로 유지한다.

### helper 출력 형식

- core helper 출력은 `상태:`와 `진행 상태:` 두 줄로 시작한다.
- `진행 상태:` 형식: `phase=<...>; last=<...>; next=<...>`
- interrupt/close 요청 시: 새 작업을 중지하고 `final`을 우선 flush한다. 불가능하면 `checkpoint`를 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.

### STATUS.md

- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 메인 스레드가 helper 요약을 통합해 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.

## 리뷰와 planning role

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| main-thread | 쓰기 가능 | 전략, focused validation, 상태 통합/기록 |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | quality preflight 승격 판정과 구조/검증 게이트 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## Internal Planning Roles

- `web-researcher`, `solution-analyst`, `product-planner`, `structure-planner`, `ux-journey-critic`, `delivery-risk-planner`, `prompt-systems-designer`
- 위 role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- 장시간 대기/폴링 감시는 built-in `monitor`만 사용하고 repo-managed projection은 만들지 않는다.
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
- `module-structure-gatekeeper`는 비trivial code diff 이후 실행한다.
  - FAIL 판정은 공통 구조 관점에서 P1로 취급한다.
  - 이미 soft limit를 넘긴 파일에 additive diff를 더하면 strong mode에서 FAIL이다.
- `frontend-structure-gatekeeper`는 비trivial frontend diff(`*.tsx`, `*.jsx`, `src/components/**`, `src/hooks/**`, `src/features/**`) 이후 추가 실행한다.
  - FAIL 판정은 React 구조 관점에서 P1로 취급한다.
  - 이미 soft limit를 넘긴 React 파일에 additive diff를 더하면 strong mode에서 FAIL이다.
- `type-specialist`는 shared/public types, generics, public contract 변경 시 실행한다.
- `test-engineer`는 회귀 리스크가 크거나 테스트 커버리지 공백이 있을 때 실행한다.

## 서브 에이전트 응답 가이드라인

- quality preflight/reviewer helper는 `품질판정: keep-local | orchestrated-task`를 포함한다.
- `orchestrated-task`일 때는 `work_type`와 핵심 `impact_flags`를 함께 적는다.
- 필수 항목은 `핵심결론`, `근거`다.
- 선택 항목은 `리스크`, `권장 다음 행동`, `추가 확인 필요`다.
- 원문 출력이 필요하면 최소 발췌만 포함하고 소스 경로를 명시한다.

## 언어 및 스타일

- 설명은 기본적으로 한국어를 사용한다.
- 코드 식별자, 명령어, 로그는 원어를 유지한다.
