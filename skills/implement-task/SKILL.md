---
name: implement-task
description: >
  Execute the next approved slice from `task.yaml` bundles or legacy `PLAN.md` fallback.
  "구현해줘", "다음 단계 진행해", "계속해" 요청에서 사용하며, `slice implementation ->
  main focused validation -> commit -> STATUS.md update` 흐름으로 다음 slice를 진행한다.
---

# Implement Task

승인된 task bundle 또는 legacy plan의 다음 실행 slice를 구현한다.

## Trigger

- `구현해줘`
- `다음 단계 진행해`
- `계속해`
- 설계가 끝난 bundle 또는 legacy task의 실행 요청

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- `delivery_strategy=ui-first`면 `task.yaml.source_of_truth.ux = UX_SPEC.md`, `task.yaml.source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, `task.yaml.source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`
- `task.yaml.source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`
- legacy fallback only: `PLAN.md`, `STATUS.md`
- blocking 판정이 필요한 bundle이면 `SPEC_VALIDATION.md`

## Task Selection

- 여러 active task 폴더가 공존하는 것은 정상 경로다.
- path 미지정이면 먼저 active 후보를 만든다.
- 후보가 정확히 1개일 때만 자동 선택한다.
- 후보가 2개 이상이면 항상 사용자에게 task를 확인받고 자동 실행하지 않는다.

## Core Flow

1. `STATUS.md`를 먼저 읽고 bundle vs legacy를 판정한다. `STATUS.md`가 없으면 고정 템플릿 섹션으로 생성하고, `task.yaml`가 있으면 bundle을 우선하며 `PLAN.md` fallback은 legacy task에만 허용한다.
2. path/slug 지정이 있으면 해당 task를 사용하고, 미지정일 때는 위 candidate rule을 그대로 적용한다.
3. bundle이면 `task.yaml.success_criteria`, `major_boundaries`, `delivery_strategy`를 구현 계약으로 유지하고 `SPEC_VALIDATION.md` blocking issue를 확인한다. `task.yaml.source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`를 선행 입력으로 함께 읽는다.
4. `delivery_strategy=ui-first`면 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/manifest.json`을 함께 읽는다. `SLICE-1`은 checklist/layout/token/screen-flow와 interaction/a11y/microcopy를 읽고, `SLICE-2`는 keyboard/focus, live semantics, state matrix/fixture, degradation, task-based approval criteria를 읽는다.
5. 현재 slice 범위를 고정한 뒤 structure preflight 후 code/doc diff를 적용한다. `split-first trigger`가 켜지면 기존 파일 append 대신 같은 slice 안에서 분해 경계를 먼저 고정하고, 범위를 줄이지 못하면 `exact split proposal`로 되돌린다.
6. 브라우저 재현이나 시각 증거가 필요할 때만 `browser-explorer`를 사용하고 handoff에는 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
7. 메인 스레드가 focused validation을 실행한다. 기본값은 `타깃 검증 1개 + 저비용 체크 1개`다.
8. 검증이 통과하면 커밋을 수행하고 `STATUS.md`를 manager-facing 요약으로 갱신한다.
9. `계속해`는 slice 1개에서 종료하고, `끝까지` 모드는 stop/replan 조건을 만날 때까지 같은 순서를 반복한다.

## Guardrails

- mixed mode(`task.yaml`와 `PLAN.md` 공존)는 구현하지 않고 중단한다.
- `validation_gate: blocking`인데 blocking issue가 남아 있으면 구현을 시작하지 않는다.
- `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, project implementation rules가 unresolved면 구현을 시작하지 않는다.
- `delivery_strategy=ui-first`면 `SLICE-1 -> SLICE-2 -> SLICE-3+` 순서를 건너뛰거나 병합하지 않고, early UI slice에 real API/integration diff를 섞지 않는다.
- `slice implementation -> main focused validation -> commit` 순서를 유지한다.
- hybrid mode default는 `small slices + run-to-boundary`다.
- slice budget이 small slices 기준(`repo-tracked files 3개 이하`, 순 diff `150 LOC 내외`)을 넘기면 `split/replan before execution`으로 되돌린다.
- focused validation이 실패하면 커밋하지 않고 slice 실패를 기록한다.
- 문서/SSOT 변경이 있으면 필요한 sync와 `--check`까지 끝난 뒤 종료한다.

## References

- 상세 실행 규칙, validation fallback, STATUS 계약: `references/execution-rules.md`

## Validation

- bundle이면 `EXECUTION_PLAN.md`, legacy면 `PLAN.md`의 검증 명령을 우선 사용한다.
- 검증 명령이 비어 있을 때만 repo-aware fallback을 사용한다.
- `skills`, `docs/policy`, `agent-registry` 같은 SSOT를 바꿨다면 대응 sync + `--check`를 실행한다.
- `skills`를 바꿨다면 `python3 scripts/sync_skills_index.py --check`를 포함한다.
- `agent-registry`를 바꿨다면 `python3 scripts/sync_agents.py --check`를 포함한다.
