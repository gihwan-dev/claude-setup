---
name: implement-task
description: >
  Implementation execution skill for long-running tasks. Use when the user says "구현해줘",
  "다음 단계 진행해", "계속해", or asks to execute based on an existing design.
  Read tasks/{task-path}/task.yaml + EXECUTION_PLAN.md + STATUS.md for new bundle tasks,
  honor `delivery_strategy`, fall back to legacy PLAN.md + STATUS.md only for older tasks,
  and execute the next slice.
---

# Workflow: Implement Task

## Goal

선택된 task bundle 또는 legacy plan 기준으로 다음 실행 slice를 구현하고 해당 `STATUS.md`를 갱신한다.
새 bundle task의 구현 계약은 `task.yaml + EXECUTION_PLAN.md + STATUS.md -> worker edit(구현 + 필요한 문서/source-of-truth 반영) -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision`이다.

## Hard Rules

- 항상 `STATUS.md`를 먼저 읽는다.
- 새 bundle task면 `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`를 먼저 읽는다.
- 새 bundle task의 `task.yaml.success_criteria`, `task.yaml.major_boundaries`, `task.yaml.delivery_strategy`는 continuity에서 확정된 계약으로 취급하고 임의 변경하지 않는다.
- legacy task에 한해서만 `PLAN.md`, `STATUS.md` fallback을 사용한다.
- mixed mode(`task.yaml`와 `PLAN.md` 공존)는 구현하지 않고 중단한다.
- 새 bundle task에서 `validation_gate: blocking`인데 `SPEC_VALIDATION.md`의 blocking issue가 해소되지 않았으면 구현을 시작하지 않는다.
- `delivery_strategy=ui-first`면 `SLICE-1`/`SLICE-2`를 병합하거나 건너뛰지 않는다.
- `delivery_strategy=ui-first`인 early UI slice에서는 real API/backend/data contract/integration diff를 허용하지 않는다.
- 여러 active task 폴더가 공존하는 것은 정상 경로다.
- `implement-task`의 code writer는 `worker` 하나다.
- writable projection은 `worker`만 허용한다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 각 slice 실행 전에는 structure preflight(대상 파일 역할, 예상 post-change LOC, split 필요 여부)를 먼저 고정한다.
- split-first trigger가 켜지면 target file append를 금지하고 같은 slice 내 추출 또는 `blocked + exact split proposal`만 허용한다.
- 종료 전 메인 스레드는 실질 영향 문서만 다시 탐색/검토한다. 기본 대상은 `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs다.
- 문서 영향 대상이 불명확할 때만 read-only helper로 후보를 좁힌다.
- 문서 변경이 필요하면 phase 1을 수행한 same `worker`가 focused validation 전에 함께 반영한다.
- `docs/policy`, `skills`, `agent-registry` 같은 SSOT를 바꿨다면 관련 generated projection sync와 대응 `--check`가 통과하기 전에는 종료하지 않는다.
- 문서 diff도 slice hard guardrail에 포함한다. 문서 반영까지 포함해 budget을 넘기면 현재 slice를 억지로 넓히지 말고 replan한다.
- 기본 실행 단위는 다음 slice 1개다.
- focused validation은 메인 스레드가 수행한다.
- verification-worker는 메인 검증 로그가 noisy/multi-step일 때만 사용한다.
- live browser reproduction, DOM/visual QA, screenshot evidence가 필요할 때만 `browser-explorer`를 선택적으로 사용한다. 이때 handoff에는 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다. `explorer`는 레포 탐색용으로만 유지한다.
- focused validation이 실패하면 해당 slice는 커밋하지 않고 즉시 중단한다.
- 각 slice는 커밋을 정확히 1회 남겨야 하며, 커밋 메시지는 한국어 conventional commit 한 줄을 사용한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 slice 실패로 기록하고 다음 slice로 넘어가지 않는다.
- slice hard guardrail: `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice로 묶는 giant mixed slice를 금지한다.
- full-repo validation은 shared/public boundary 변경 시에만 허용한다.
- `wait timeout`은 stalled와 동일하지 않다.
- `liveness gate`와 `completion gate`를 분리한다.
- close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.
- `explicit cancel`만 종료 근거다.
- `result가 더 이상 필요 없음`은 close 근거가 아니다.
- writer stall 기본 정책은 대기+점검이며 replacement writer를 투입하지 않는다.
- advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.
- 늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.
- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.
- `wait timed_out -> status running -> no result -> close`는 invalid sequence다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 취급하고 그 외에는 advisory로 취급한다.
- 리뷰 요청에서 구조 개선 계획을 새로 만드는 역할은 이 스킬이 아니라 `design-task`/reviewer에 있다. `implement-task`는 승인된 계획 실행에만 집중한다.

## Task Selection Rules

1. 사용자 지정 slug/path가 있으면 해당 task를 사용한다.
2. path 미지정이면 먼저 active 후보를 만든다. (`미완료 Next slice`가 있거나 현재 실행 가능한 task만 후보로 본다.)
3. 후보가 정확히 1개일 때만 자동 선택한다.
4. 후보가 2개 이상이면 항상 사용자에게 task를 확인받고 자동 실행하지 않는다.
5. 후보가 0개면 최근 수정 task를 참고하되 사용자 확인 전까지 실행하지 않는다.
6. 새 bundle 후보가 있으면 legacy 후보보다 bundle 후보를 우선한다.

## Mode Rules

- 사용자가 `계속해`라고 하면 현재 task의 다음 slice 1개를 수행한다.
- 사용자가 `끝까지` 또는 `stop condition 만날 때까지`를 명시하면 연속 실행 루프를 사용한다.
- 연속 실행 중 아래 조건이면 즉시 중단하고 `STATUS.md`만 갱신한다.
  - 검증 실패(커밋 시도 없음)
  - 커밋 실패(`--no-verify` 재시도 실패 포함)
  - `worker`가 `상태: blocked`를 보고함 → stop이 아니라 replan으로 전환
  - `liveness gate` 점검과 `drain grace` 이후에도 `final/checkpoint`를 받지 못함
  - bundle `SPEC_VALIDATION.md`의 blocking issue가 해소되지 않음
  - legacy `PLAN.md` 또는 bundle `EXECUTION_PLAN.md`의 stop/replan 조건 충족
  - public boundary drift 발생
  - 다음 slice 진행 전 의사결정 공백 발생

## Execution Workflow

1. 대상 task를 선택한다.
2. task mode를 판정한다. 새 bundle이면 `task.yaml + EXECUTION_PLAN.md + STATUS.md`, legacy면 `PLAN.md + STATUS.md`를 읽는다.
3. 새 bundle이면 `SPEC_VALIDATION.md`를 확인해 `validation_gate`와 blocking issue 상태를 판정한다.
4. 새 bundle의 `EXECUTION_PLAN.md`가 `Execution slices`, `Verification`, `Stop / Replan conditions` 순서를 따르는지 전제로 slice를 읽는다. `delivery_strategy=ui-first`면 `SLICE-1 -> SLICE-2 -> SLICE-3+` 순서를 고정된 구현 계약으로 읽는다.
5. `STATUS.md`가 없으면 고정 템플릿 섹션으로 파일을 생성한다.
6. phase 1에서 fresh `worker`가 edit-only로 현재 slice의 code diff를 적용한다.
7. phase 1 시작 시 `worker`는 대상 파일 역할, 예상 post-change LOC, split 필요 여부를 먼저 보고한다.
8. split-first trigger가 켜지면 same `worker`는 기존 파일 append 대신 새 모듈 추출 또는 `blocked + exact split proposal`로 되돌린다.
9. 메인 스레드는 실질 영향 문서를 판정하고 다시 탐색/검토한다. 대상이 불명확할 때만 read-only helper를 사용한다.
10. 필요한 문서 diff나 SSOT 관련 generated projection sync는 phase 1을 수행한 same `worker`가 focused validation 전에 마무리한다.
11. 메인 스레드는 `worker`의 `liveness gate`와 `completion gate`를 분리해 관찰한다. `wait timeout`만으로 stalled나 close를 판정하지 않는다.
12. 진행이 멈춘 것처럼 보이면 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서로만 처리한다.
13. 메인 스레드가 focused validation을 실행한다. 기본값은 `타깃 검증 1개 + 저비용 체크 1개`다.
14. 검증 출력이 noisy하면 `verification-worker`가 메인 검증 로그를 해석하고 pass/fail을 요약한다. commit sign-off가 불가능한 경우에만 일시적으로 semi-blocking으로 취급한다.
15. focused validation이 실패하면 커밋하지 않고 slice 실패를 기록한다.
16. focused validation이 통과하면 phase 1을 수행한 same `worker`가 commit-only로 재개한다.
17. 1차 `git commit`이 hook 실패로 막히면 same `worker`가 동일 메시지로 `git commit --no-verify`를 1회만 재시도한다.
18. 커밋이 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.
19. `STATUS.md`를 manager-facing 요약으로 갱신한다.
20. `계속해` 모드면 종료한다. `끝까지` 모드면 다음 slice를 다시 읽고 6번부터 반복한다.

## Default Validation Fallback (Repo-Aware)

- 새 bundle task면 `EXECUTION_PLAN.md`에 있는 검증 명령을 우선 사용한다.
- legacy task면 `PLAN.md`에 있는 검증 명령을 우선 사용한다.
- 문서에 검증 명령이 비어 있을 때만 repo-aware fallback을 사용한다.
- focused validation owner는 메인 스레드다.
- 기본 focused validation은 `타깃 검증 1개 + 저비용 체크 1개`를 사용한다.
- full-repo validation은 shared/public boundary 변경으로 범위 확장이 필요한 경우에만 사용한다.
- JS/TS repo 추론: `package.json` + lockfile(`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`)를 기준으로 package manager를 고른다.
- Python repo 추론: `pyproject.toml` 또는 `tests/`/`test_*.py`를 기준으로 `python3 -m unittest discover`를 후보로 본다.
- 추론된 manager/도구에서 존재하는 스크립트(예: `typecheck`, `lint`, `test`)만 실행한다.
- 안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.
- SSOT sync/check가 필요한 경우 아래 repo-aware fallback을 사용한다.
- `docs/policy` 변경 시 `python3 scripts/sync_instructions.py` 후 `python3 scripts/sync_instructions.py --check`를 사용한다.
- `skills` 변경 시 `python3 scripts/sync_skills_index.py` 후 `python3 scripts/sync_skills_index.py --check`를 사용한다.
- `agent-registry` 변경 시 `python3 scripts/sync_agents.py` 후 `python3 scripts/sync_agents.py --check`를 사용한다.

## Lane and Agent Rules

- `implement-task`의 code writer는 `worker` 하나다.
- writable projection은 `worker`만 허용한다.
- 오케스트레이터는 slice 선택, 문서 영향 판정, focused validation 실행, stop/replan 판정, 상태 기록을 수행한다.
- read-only helper fan-out은 탐색/리뷰/로그 해석이 필요할 때만 사용하고, 문서 영향 대상이 불명확할 때만 문서 검토 보조로 사용한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.
- 필요한 문서 diff는 phase 1을 수행한 same `worker`가 focused validation 전에 반영한다.
- noisy validation일 때만 `verification-worker`를 사용하고, 메인 검증 raw log 해석은 verifier가 담당한다.
- phase 1을 수행한 same `worker`가 commit-only를 수행한다.
- 같은 slice에는 phase 1을 수행한 same `worker`만 commit-only를 수행한다.
- `delivery_strategy=ui-first`면 early UI slice에 real API/integration diff를 섞지 않고 다음 slice로 넘긴다.
- `wait timeout`은 stalled와 동일하지 않으며 replacement writer를 트리거하지 않는다.
- `module-structure-gatekeeper`는 비trivial code diff 이후 자동 reviewer로 실행한다.
- `frontend-structure-gatekeeper`는 비trivial frontend diff에서 추가 자동 reviewer로 실행한다.
- `EXECUTION_PLAN.md`의 각 slice는 `split decision`과 target-file append 금지 trigger를 포함해야 한다.
- `code-quality-reviewer`, `architecture-reviewer`, `type-specialist`, `test-engineer`는 기존 AGENTS 트리거를 따른다.

## STATUS Template (Fixed Sections)

```markdown
# Current slice
# Done
# Decisions made during implementation
# Verification results
# Known issues / residual risk
# Next slice
```

## STATUS Update Rules

- `# Current slice`: 이번 실행 대상 slice를 적는다.
- `# Done`: 구현 세부 나열 대신 완료된 결과와 사용자/시스템 영향만 요약한다.
- `# Decisions made during implementation`: 다음 slice 또는 공개 경계에 영향을 주는 의사결정만 적고, 문서 영향 판단 결과도 함께 남긴다.
- `# Verification results`: 검증 명령, pass/fail, 문서/SSOT sync-check 결과, 커밋 시도 결과(기본 커밋/`--no-verify` 재시도 여부), 핵심 실패 원인만 적는다. raw log를 붙이지 않는다.
- `# Known issues / residual risk`: 남은 위험과 미해결 이슈를 적는다.
- `# Next slice`: 바로 실행할 수 있도록 목표, 선행조건, 먼저 볼 경계를 적는다.
- `STATUS.md`를 최초 생성한 실행에서는 템플릿 생성 사실을 `# Done` 또는 `# Decisions made during implementation`에 기록한다.
- design 단계에서 생성된 초기 bundle은 `# Current slice`가 `Not started.`, `# Next slice`가 `SLICE-1`이어야 한다.

## Non-Goals

- 레거시 문서/흐름 호환 로직을 무한 확장하지 않는다.
- 승인되지 않은 bundle 구조 확장을 임의로 추가하지 않는다.
