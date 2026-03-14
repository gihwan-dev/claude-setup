---
name: design-task
description: >
  Large or ambiguous non-trivial task planning skill. Use when the user asks to "설계해줘",
  "계획 세워줘", "어떻게 쪼갤지 정리해줘", or explicitly asks for no code changes on work
  that should enter the long-running path. Build or update a tasks/{task-path}/task.yaml
  bundle via a continuity gate, derive `delivery_strategy` for UI-impact work, generate
  SPEC_VALIDATION.md, and keep legacy PLAN.md tasks only as fallback compatibility.
---

# Workflow: Design Task

## Goal

사용자 요청을 long-running task bundle로 설계하고 continuity gate로 기존 task 재사용 여부를 판정한 뒤
`tasks/<task-path>/task.yaml` 중심 문서 세트를 생성 또는 갱신한다.
설계 단계에서는 코드 수정을 금지한다.
greenfield/new-project work면 구현 전에 `$bootstrap-project-rules` handoff가 필요할 수 있다.

## Hard Rules

- 코드/설정/테스트 파일을 수정하지 않는다.
- read-only 탐색만 수행한다.
- 새 task 출력은 flat `tasks/<task-path>/` bundle이다.
- 새 task에는 `PLAN.md`를 만들지 않는다.
- legacy `PLAN.md`/`STATUS.md` task는 fallback compatibility로만 유지한다.
- `quality preflight` 결과는 `keep-local` 또는 `orchestrated-task`로 기록한다.
- `keep-local`이면 기존 fast/deep-solo/delegated lane으로 되돌리고 여기서 장기 실행 계획을 시작하지 않는다.
- 기존 task 재사용은 예외다. 새 task 생성이 기본이다.
- 후보가 2개 이상이면 자동 재사용하지 않는다. 사용자 확인 필요를 `Task continuity`에 기록한다.
- continuity gate에서는 post-design bootstrap supplement(`IMPLEMENTATION_CONTRACT.md`, `source_of_truth.implementation`)를 normalize하고 task identity 차이로 보지 않는다.
- `reuse-existing` 경로에서 기존 bundle에 bootstrap supplement가 있으면 삭제하지 않고 보존한다.
- `task.yaml.delivery_strategy`는 필수고 `standard` 또는 `ui-first`만 허용한다.
- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `delivery_strategy=ui-first`로 고정한다.
- `delivery_strategy=ui-first`면 `UX_SPEC.md`를 UX source of truth로 고정하고 `UI -> local state/mock -> real API/integration` slice 순서를 반드시 유지한다.
- greenfield/new-project 설계에서 repo-level implementation rules가 아직 없으면 `SPEC_VALIDATION.md`에 `$bootstrap-project-rules` 필요 blocking issue를 남긴다.
- 기존 TS/JS/React 코드 작업이면 structure preflight(대상 파일 역할, 예상 post-change LOC, split-first 필요 여부)를 quality preflight에 포함한다.
- split-first trigger가 켜지면 기존 파일 append 전제 설계를 금지하고 분해안을 먼저 만든다.
- 각 execution slice는 변경 경계, 예상 파일 수, validation owner, focused validation plan, stop/replan 조건을 포함한다.
- 각 execution slice는 `split decision`과 target-file append 금지 trigger를 함께 포함한다.
- slice 설계 기본 guardrail은 small slices 기준으로 `repo-tracked files 3개 이하`, 순 diff `150 LOC 내외`다. 이를 넘기면 `split/replan before spawn`으로 되돌린다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice로 묶는 giant mixed slice를 금지한다.

## Required References

- continuity gate가 필요할 때만 `${SKILL_DIR}/references/plan-continuity-rules.md`를 읽는다.
- 새 bundle의 문서 선택 규칙과 gate는 `${SKILL_DIR}/references/task-bundle-rules.md`를 읽는다.
- planning role fallback overlay가 필요할 때만 `${SKILL_DIR}/references/planning-role-cards.md`를 읽는다.

## Inputs

- 사용자 요청
- 코드베이스 read-only 탐색 결과
- 사용자가 지정한 문서/경로
- 기존 `tasks/<task-path>/task.yaml`, `README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, `STATUS.md`
- 기존 legacy `tasks/<task-path>/PLAN.md`, `tasks/<task-path>/STATUS.md`

## Task Path Selection

1. 사용자가 path를 직접 지정하면 continuity gate 없이 그대로 사용한다.
2. `continue`, `update`, `replan`, `기존 계획 이어서` 같은 continuation 표현이 있으면 기존 task 후보를 우선 비교한다.
3. 새 bundle 후보가 있으면 `task.yaml`을 기준으로 continuity gate를 적용한다.
4. 새 bundle 후보가 없을 때만 legacy `PLAN.md`를 fallback으로 비교한다.
5. `goal + success_criteria + work_type + impact_flags + normalized required_docs + major_boundaries + delivery_strategy`가 모두 같은 단일 후보일 때만 해당 task path를 재사용한다.
6. 위 비교에서 하나라도 다르거나 goal differs로 판정되면 새 flat task path를 만든다.
7. 새 path는 현재 goal을 hyphen-case로 정규화한 base slug를 사용한다.
8. base slug가 충돌하면 먼저 현재 계획의 focus를 드러내는 접미사(`-task-identity`, `-plan-split`, `-api`, `-ui`)를 붙인다.
9. focus suffix까지 충돌할 때만 마지막 fallback으로 `-v2`를 붙인다.

## Workflow

1. 요청의 목표/제약/성공 기준을 추출한다.
2. 관련 코드, 문서, 기존 `tasks/` 문서를 read-only로 조사하고 quality preflight 근거를 수집한다.
3. 기존 코드 작업이면 structure preflight를 수행하고 `split-first` 여부를 기록한다.
4. quality preflight verdict와 후속 경로를 기록한다.
5. `orchestrated-task`가 아니면 여기서 종료하고 기존 lane으로 되돌린다.
6. continuation 표현 또는 관련 task 흔적이 있으면 continuity gate를 수행한다.
7. `Task continuity`에 `decision`, `compared tasks`, `reason`, `chosen task path`를 기록한다. bootstrap supplement normalization 또는 preserved가 있으면 그 사실도 함께 기록한다.
8. `work_type`를 `feature`, `bugfix`, `refactor`, `migration`, `prototype`, `ops` 중 하나로 결정한다.
9. 핵심 `impact_flags`를 고정하고 `delivery_strategy`를 `standard` 또는 `ui-first`로 결정한다.
10. `${SKILL_DIR}/references/task-bundle-rules.md` 기준으로 `required_docs`를 결정한다. `reuse-existing`인데 기존 bundle에 bootstrap supplement가 있으면 `IMPLEMENTATION_CONTRACT.md`를 보존한다.
11. `task.yaml`을 machine entry point로 작성한다. `reuse-existing`인데 기존 bundle에 `source_of_truth.implementation`이 있으면 optional pointer도 보존한다.
12. `README.md`를 사람용 landing 문서로 작성한다.
13. `delivery_strategy=ui-first`면 `source_of_truth.ux = UX_SPEC.md`를 고정하고 화면 구조, 주요 상태, mock 전략이 정리되기 전에는 integration slice를 만들지 않는다.
14. `EXECUTION_PLAN.md`에 `Execution slices`, `Verification`, `Stop / Replan conditions` level-1 section을 유지하며 bounded slice, focused validation, split decision을 작성한다.
15. `delivery_strategy=ui-first`면 `SLICE-1`은 static/visual UI, `SLICE-2`는 local state/mock, `SLICE-3+`는 real API/integration으로 고정하고 `SLICE-1`/`SLICE-2`에는 real API/integration 금지를 명시한다.
16. `SPEC_VALIDATION.md`를 항상 생성하고 `blocking` 또는 `advisory` verdict를 기록한다. `delivery_strategy=ui-first`인데 UI state/flow 미정의, mock 전략 부재, UX 방향 미확정이 남아 있으면 `Blocking issues`에 기록한다. greenfield/new-project에서 repo baseline implementation rules가 없으면 `$bootstrap-project-rules` 실행 요구를 `Blocking issues`에 남긴다.
17. `STATUS.md`를 초기 템플릿으로 만들고 `Current slice`는 `Not started.`, `Next slice`는 `SLICE-1`로 채운다.
18. `source_of_truth`와 traceability IDs를 문서에 반영한다. post-design bootstrap 이후 `source_of_truth.implementation = IMPLEMENTATION_CONTRACT.md`가 추가될 수 있음을 task `README.md`와 `SPEC_VALIDATION.md`에서 handoff로 남긴다.
19. legacy task를 재사용할 때만 기존 `PLAN.md`를 갱신하고, 새 task에는 bundle 문서만 사용한다.

## Multi-Agent Usage (Optional)

필요할 때만 read-only 병렬 에이전트를 사용한다.

### Planning Roles (Internal-Only Priority)

planning role은 internal fan-out 전용이다.
user-facing install/projection 대상으로 취급하지 않는다.

- `web-researcher`
- `solution-analyst`
- `product-planner`
- `structure-planner`
- `ux-journey-critic`
- `delivery-risk-planner`
- `prompt-systems-designer`

기존 TS/JS/React 코드의 quality preflight는 `explorer`를 기본으로 사용한다.
구조 냄새나 `split-first`가 보이면 `structure-planner`, `complexity-analyst`, `test-engineer`를 추가해 분해 경계를 먼저 정리한다.
public/shared boundary 리스크가 보이면 `architecture-reviewer`를 fan-out해 boundary 결정을 먼저 고정한다.
`delivery_strategy=ui-first`면 `ux-journey-critic`를 우선하고 goal/scope가 모호할 때만 `product-planner`, 구조 분해가 필요할 때만 `structure-planner`를 추가한다.
AI/agent workflow planning이면 `web-researcher`를 먼저 사용하고 OpenAI, Anthropic 같은 official vendor docs를 우선 출처로 고정한다.
planning fan-out은 독립적인 lens에만 제한하고 광범위한 멀티에이전트 확장은 하지 않는다.

### Fallback Rules (Runtime Unavailable)

- `web-researcher`: 메인 스레드에서 직접 웹 조사 수행 (출처 링크 + 날짜 + 사실/추정 구분)
- 나머지 planning role: `explorer` + role card overlay 사용
- `architecture-reviewer`: 경계/모듈 영향 점검
- `type-specialist`: 공개 타입/계약 영향 점검
- `test-engineer`: 검증 시나리오 도출

### Planning Lens Classification

- `external-benchmark`: 경쟁사/최신 대안 조사 (`web-researcher`, AI/agent workflow면 official vendor docs 우선)
- `solution-comparison`: 구현 옵션 비교 (`solution-analyst`)
- `product-clarification`: 목표/범위/수용 기준 정리 (`product-planner`)
- `module-structure`: 공통 모듈 분해/책임 경계 설계 (`structure-planner`)
- `ux-journey`: 사용자 흐름/마찰 점검 (`ux-journey-critic`)
- `delivery-risk`: 배포/운영 리스크 점검 (`delivery-risk-planner`)
- `prompt-system`: 프롬프트/도구 경계 설계 (`prompt-systems-designer`)

## Required Bundle Content

새 task bundle은 최소 아래 다섯 문서를 포함한다.

- `task.yaml`
- `README.md`
- `EXECUTION_PLAN.md`
- `SPEC_VALIDATION.md`
- `STATUS.md`

전문 문서(`PRD.md`, `UX_SPEC.md`, `TECH_SPEC.md`, `BUG_REPORT.md`, `ROOT_CAUSE.md`, `MIGRATION.md`, `RUNBOOK.md` 등)는
`${SKILL_DIR}/references/task-bundle-rules.md`의 doc selection matrix에 따라 추가한다.

## Required Sections / Fields

- `SPEC_VALIDATION.md`는 `Requirement coverage`, `UX/state gaps`, `Architecture/operability risks`, `Slice dependency risks`, `Blocking issues`, `Proceed verdict` 순서를 유지한다.
- `STATUS.md`는 `Current slice`, `Done`, `Decisions made during implementation`, `Verification results`, `Known issues / residual risk`, `Next slice`를 유지한다.
- `task.yaml`은 `task`, `goal`, `success_criteria`, `major_boundaries`, `work_type`, `impact_flags`, `required_docs`, `source_of_truth`, `ids`, `delivery_strategy`, `validation_gate`, `current_phase`를 반드시 포함한다.
- post-design bootstrap이 적용되면 `required_docs`와 `source_of_truth`에 `IMPLEMENTATION_CONTRACT.md`가 추가될 수 있다.
- `EXECUTION_PLAN.md`는 `Execution slices`, `Verification`, `Stop / Replan conditions` 순서를 유지한다.

## Output Quality Checklist

- continuity gate 결과와 새 task 생성/재사용 근거가 `Task continuity`에 반영되었는가?
- continuity 비교에서 `IMPLEMENTATION_CONTRACT.md`와 `source_of_truth.implementation`을 normalize하고 identity 차이로 취급하지 않았는가?
- `reuse-existing` 경로라면 기존 bootstrap supplement를 보존하고 `Task continuity`에 preserved를 남겼는가?
- `work_type`와 핵심 `impact_flags`가 고정되었는가?
- `delivery_strategy`가 고정되고 continuity 비교 기준에 반영되었는가?
- `required_docs`가 실제 bundle 구조와 일치하는가?
- `SPEC_VALIDATION.md` verdict가 `blocking` 또는 `advisory`로 명확한가?
- greenfield/new-project이면 `$bootstrap-project-rules` handoff 필요 여부가 `Blocking issues`에 명확한가?
- 각 slice에 change boundary / file budget / validation owner / stop-replan trigger가 있는가?
- 각 slice에 `split decision`과 target-file append 금지 trigger가 있는가?
- `delivery_strategy=ui-first`면 `SLICE-1/2/3+` 순서와 real API/integration 금지 경계가 명시되었는가?
- traceability ID가 `REQ`, `SCR`, `FLOW`, `ADR`, `AC`, `SLICE`, `RISK` 체계를 따르는가?
