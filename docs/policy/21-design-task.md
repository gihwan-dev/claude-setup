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
