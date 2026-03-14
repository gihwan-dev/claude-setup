# Task Bundle Rules

`design-task`가 새 long-running task를 만들거나 갱신할 때만 이 파일을 읽는다.
목표는 `PLAN.md` 단일 문서 대신 사람용 문서와 machine entry를 분리한 task bundle을 고정하는 것이다.

## Core Docs

모든 새 task bundle에는 아래 문서를 만든다.

- `task.yaml`
- `README.md`
- `EXECUTION_PLAN.md`
- `SPEC_VALIDATION.md`
- `STATUS.md`

`task.yaml`은 machine entry point다.
`README.md`는 사람이 보는 landing 문서다.
새 task에는 `PLAN.md`를 만들지 않는다.

## `task.yaml`

필수 키:

- `task`
- `goal`
- `success_criteria`
- `major_boundaries`
- `work_type`
- `impact_flags`
- `required_docs`
- `source_of_truth`
- `ids`
- `delivery_strategy`
- `validation_gate`
- `current_phase`

`required_docs`는 `task.yaml` 자신을 제외한 실제 bundle 문서/디렉터리 집합을 적는다.
`source_of_truth`는 실제 파일 경로만 가리킨다.
`success_criteria`와 `major_boundaries`는 continuity gate 비교에 직접 사용한다.
`delivery_strategy`도 continuity gate 비교에 직접 사용한다.
post-design bootstrap이 적용되면 `required_docs`에 `IMPLEMENTATION_CONTRACT.md`가 추가될 수 있고,
`source_of_truth.implementation`이 optional pointer로 생길 수 있다.
reuse-existing로 기존 bundle을 갱신할 때 이미 존재하는 bootstrap supplement는 삭제하지 않고 보존한다.

## Work Types

- `feature`
- `bugfix`
- `refactor`
- `migration`
- `prototype`
- `ops`

## Delivery Strategies

- `standard`
- `ui-first`

파생 규칙:

- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `ui-first`
- 그 외는 `standard`
- `ui-first`면 `reference-pack`을 먼저 실행해 `DESIGN_REFERENCES/`를 채우고, `figma-less-ui-design`이 `UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md`를 작성한다.
- 기존 design system, shipped UI, brand guide, Figma가 있으면 packet은 새 style invention이 아니라 `reuse + delta`를 기록한다.
- `ui-first`면 UX 방향, behavior/a11y/live 계약, state/fixture 전략이 정리되기 전에는 integration slice를 만들지 않는다.

## UI Planning Packet (`UX_SPEC.md`)

`delivery_strategy=ui-first`면 `UX_SPEC.md`는 아래 heading 순서를 그대로 유지한다.

- `Goal/Audience/Platform`
- `30-Second Understanding Checklist`
- `Visual Direction + Anti-goals`
- `Reference Pack (adopt/avoid)`
- `Glossary + Object Model`
- `Layout/App-shell Contract`
- `Token + Primitive Contract`
- `Screen + Flow Coverage`
- `Implementation Prompt/Handoff`

## UX Behavior & Accessibility (`UX_BEHAVIOR_ACCESSIBILITY.md`)

`delivery_strategy=ui-first`면 `UX_BEHAVIOR_ACCESSIBILITY.md`는 아래 heading 순서를 그대로 유지한다.

- `Interaction Model`
- `Keyboard + Focus Contract`
- `Accessibility Contract`
- `Live Update Semantics`
- `State Matrix + Fixture Strategy`
- `Large-run Degradation Rules`
- `Microcopy + Information Expression Rules`
- `Task-based Approval Criteria`

## Reference Pack (`DESIGN_REFERENCES/`)

`delivery_strategy=ui-first`면 `DESIGN_REFERENCES/`는 아래를 포함한다.

- `shortlist.md`
- `manifest.json`
- `raw/`
- `curated/`

추가 규칙:

- `ux-journey-critic` planning fan-out은 mandatory 기본값이다.
- `reference-pack` advisory skill은 `ui-first` planning에서 항상 자동 실행한다.
- `product-planner`, `web-researcher`, `solution-analyst`, `structure-planner`, `architecture-reviewer`는 조건이 있을 때만 추가한다.
- `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`, `Interaction Model`, `Accessibility Contract`, `Microcopy + Information Expression Rules`는 `SLICE-1` 진입 근거다.
- `Keyboard + Focus Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, `Task-based Approval Criteria`는 `SLICE-2` 진입 근거다.
- `source_of_truth.ux = UX_SPEC.md`, `source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, `source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`를 기록한다.

## Impact Flags

- `ui_surface_changed`
- `workflow_changed`
- `architecture_significant`
- `public_contract_changed`
- `data_contract_changed`
- `operability_changed`
- `high_user_risk`

## Traceability IDs

- `requirement_prefix: REQ`
- `screen_prefix: SCR`
- `flow_prefix: FLOW`
- `adr_prefix: ADR`
- `acceptance_prefix: AC`
- `slice_prefix: SLICE`
- `risk_prefix: RISK`

문서 간 연결은 복붙이 아니라 ID 참조로만 유지한다.

## Doc Selection Matrix

### `feature`

기본 문서:

- `PRD.md`
- `ACCEPTANCE.feature`

추가 규칙:

- `ui_surface_changed` 또는 `workflow_changed`가 있으면 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/`
- `architecture_significant`, `public_contract_changed`, `data_contract_changed`, `operability_changed` 중 하나가 있으면 `TECH_SPEC.md`
- `architecture_significant`가 있으면 `ADRs/`
- `public_contract_changed`가 있으면 기본 계약 문서는 `openapi.yaml`
- `data_contract_changed`가 있으면 기본 계약 문서는 `schema.json`

### `bugfix`

기본 문서:

- `BUG_REPORT.md`
- `ROOT_CAUSE.md`
- `ACCEPTANCE.feature`

추가 규칙:

- `high_user_risk`, `public_contract_changed`, `data_contract_changed` 중 하나가 있으면 `REGRESSION.md`

### `refactor`

기본 문서:

- `CURRENT_STATE.md`
- `TARGET_STATE.md`

추가 규칙:

- architecture/public/data/operability 플래그가 있으면 `TECH_SPEC.md`
- `ui_surface_changed`, `workflow_changed`, `public_contract_changed`, `high_user_risk` 중 하나가 있으면 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/`, `ACCEPTANCE.feature`

### `migration`

기본 문서:

- `TECH_SPEC.md`
- `MIGRATION.md`
- `VERIFICATION.md`
- `ROLLBACK.md`

추가 규칙:

- `public_contract_changed`가 있으면 `openapi.yaml`
- `data_contract_changed`가 있으면 `schema.json`

### `prototype`

기본 문서:

- `PRD.md`
- `VERIFICATION.md`

추가 규칙:

- `ui_surface_changed` 또는 `workflow_changed`가 있으면 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/`
- architecture/public/data/operability 플래그가 있으면 `TECH_SPEC.md`
- `public_contract_changed`, `data_contract_changed`, `high_user_risk` 중 하나가 있으면 `ACCEPTANCE.feature`

### `ops`

기본 문서:

- `CHANGE_PLAN.md`
- `RUNBOOK.md`
- `ROLLBACK.md`
- `VERIFICATION.md`

## `SPEC_VALIDATION.md`

항상 생성하고 아래 level-1 heading 순서를 유지한다.

- `Requirement coverage`
- `UX/state gaps`
- `Architecture/operability risks`
- `Slice dependency risks`
- `Blocking issues`
- `Proceed verdict`

gate 규칙:

- `ui_surface_changed`, `workflow_changed`, `architecture_significant`, `public_contract_changed`, `data_contract_changed`, `operability_changed`, `high_user_risk` 중 하나가 있으면 `blocking`
- 위 플래그가 없어도 설계 문서가 3종 이상이면 `blocking`
- 그 외는 `advisory`

추가 규칙:

- greenfield/new-project 설계인데 repo baseline implementation rules(`docs/ai/ENGINEERING_RULES.md`)가 아직 없으면 `Blocking issues`에 `$bootstrap-project-rules` 실행 요구를 남긴다.
- `ui-first`인데 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/manifest.json` 중 하나라도 비어 있거나, 30-second checklist/glossary/interaction/a11y/live/degradation/task-based approval이 빠져 있으면 `Blocking issues`에 기록한다.
- 기존 shipped UI/Figma/design system이 명확한 경우 reference capture 부족은 advisory로 낮출 수 있지만, 그 판단 근거를 남겨야 한다.
- 이 blocking issue는 design 단계에서 자동 해소하지 않는다. post-design bootstrap이 완료된 뒤에만 cleared로 바꾼다.

## `EXECUTION_PLAN.md`

아래 level-1 heading 순서를 유지한다.

- `Execution slices`
- `Verification`
- `Stop / Replan conditions`

`Execution slices` 안의 각 slice는 최소 아래 항목을 포함한다.

- Change boundary
- Expected files
- Validation owner
- Focused validation plan
- Stop / Replan trigger

`delivery_strategy=ui-first`면 추가 규칙:

- `SLICE-1`: static/visual UI, information architecture, copy, navigation, visual shell만 다룬다. real API/integration 금지.
- `SLICE-2`: local interaction, mock data, loading/empty/error/permission/responsive/a11y state만 다룬다. real API/integration 금지.
- `SLICE-3+`: real API/backend/data contract/integration과 회귀 보강을 다룬다.
- `SLICE-1` 미승인 또는 `SLICE-2` 상태 모델 미정이면 다음 slice 진입을 stop/replan으로 막는다.

## `README.md`

한 페이지로 유지한다.

- Goal
- Document map
- Key decisions
- Validation gate status
- Implementation slice order

greenfield/new-project 설계라면 `Document map` 또는 `Validation gate status`에 post-design bootstrap handoff를 함께 남긴다.
bootstrap 이후에는 `IMPLEMENTATION_CONTRACT.md`가 document map에 추가될 수 있다.
reuse-existing 경로에서 bootstrap supplement를 유지했다면 `Task continuity` 또는 `Key decisions`에 preserved 사실을 남긴다.

`delivery_strategy=ui-first`면 `Implementation slice order`는 `SLICE-1 -> SLICE-2 -> SLICE-3+` 순서를 그대로 반영한다.

## `STATUS.md`

설계 단계에서 초기 템플릿을 미리 만든다.
`Current slice`는 `Not started.`, `Next slice`는 `SLICE-1`로 고정한다.
