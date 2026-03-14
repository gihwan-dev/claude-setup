---
name: implement-task
description: >
  Execute the next approved slice from `task.yaml` bundles or legacy `PLAN.md` fallback.
  "구현해줘", "다음 단계 진행해", "계속해" 요청에서 사용하며, `worker edit-only -> main
  focused validation -> same-worker commit-only -> STATUS.md update` 흐름으로 다음 slice를 진행한다.
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
- `task.yaml.source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`
- legacy fallback only: `PLAN.md`, `STATUS.md`
- blocking 판정이 필요한 bundle이면 `SPEC_VALIDATION.md`

## Core Flow

1. `STATUS.md`를 먼저 읽고 bundle vs legacy를 판정한다. `STATUS.md`가 없으면 고정 템플릿 섹션으로 생성하고, `task.yaml`가 있으면 bundle을 우선하며 `PLAN.md` fallback은 legacy task에만 허용한다.
2. path/slug 지정이 있으면 해당 task를 사용하고, 미지정일 때 후보가 2개 이상이면 사용자 확인 전까지 자동 실행하지 않는다.
3. bundle이면 `task.yaml.success_criteria`, `major_boundaries`, `delivery_strategy`를 구현 계약으로 유지하고 `SPEC_VALIDATION.md` blocking issue를 확인한다. `task.yaml.source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`를 선행 입력으로 함께 읽는다.
4. 현재 slice 범위를 고정한 뒤 `worker` 하나가 structure preflight 후 edit-only로 code/doc diff를 적용한다.
5. 메인 스레드가 focused validation을 실행한다. 기본값은 `타깃 검증 1개 + 저비용 체크 1개`다.
6. 검증이 통과하면 같은 `worker`가 commit-only로 재개하고 `STATUS.md`를 manager-facing 요약으로 갱신한다.
7. `계속해`는 slice 1개에서 종료하고, `끝까지` 모드는 stop/replan 조건을 만날 때까지 같은 순서를 반복한다.

## Guardrails

- mixed mode(`task.yaml`와 `PLAN.md` 공존)는 구현하지 않고 중단한다.
- `validation_gate: blocking`인데 blocking issue가 남아 있으면 구현을 시작하지 않는다.
- `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, project implementation rules가 unresolved면 구현을 시작하지 않는다.
- `delivery_strategy=ui-first`면 `SLICE-1 -> SLICE-2 -> SLICE-3+` 순서를 건너뛰거나 병합하지 않고, early UI slice에 real API/integration diff를 섞지 않는다.
- code writer는 `worker` 하나만 허용한다. same-slice second writer, replacement writer, broad setup handoff는 허용하지 않는다.
- `worker edit-only -> main focused validation -> same-worker commit-only` 순서를 유지한다.
- slice budget이 small slices 기준(`repo-tracked files 3개 이하`, 순 diff `150 LOC 내외`)을 넘기면 split/replan으로 되돌린다.
- focused validation이 실패하면 커밋하지 않고 slice 실패를 기록한다.
- 문서/SSOT 변경이 있으면 필요한 sync와 `--check`까지 끝난 뒤 종료한다.

## References

- 상세 실행 규칙, liveness/cancel 경로, validation fallback, STATUS 계약: `references/execution-rules.md`

## Validation

- bundle이면 `EXECUTION_PLAN.md`, legacy면 `PLAN.md`의 검증 명령을 우선 사용한다.
- 검증 명령이 비어 있을 때만 repo-aware fallback을 사용한다.
- `skills`, `docs/policy`, `agent-registry` 같은 SSOT를 바꿨다면 대응 sync + `--check`를 실행한다.
