---
name: implement-task
description: >
  Implementation execution skill for long-running tasks. Use when the user says "구현해줘",
  "다음 단계 진행해", "계속해", or asks to execute based on an existing design.
  Read tasks/{task-slug}/PLAN.md, execute the next slice, and always update tasks/{task-slug}/STATUS.md.
---

# Workflow: Implement Task

## Goal

`tasks/<task-slug>/PLAN.md` 기준으로 실행 슬라이스를 구현하고, `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision` 계약을 유지한다.

## Hard Rules

- 항상 `PLAN.md`와 기존 `STATUS.md`를 먼저 읽는다.
- `PLAN.md`가 없으면 구현하지 않고 `design-task`를 먼저 수행하도록 유도한다.
- `STATUS.md`가 없으면 고정 템플릿 섹션으로 `tasks/<task-slug>/STATUS.md`를 먼저 생성한 뒤 실행 기록을 채운다.
- `implement-task`는 항상 delegated lane으로 실행한다. fast lane/deep solo를 이 스킬에서 허용하지 않는다.
- 코드 수정은 `worker`만 수행한다. 오케스트레이터는 코드 수정을 수행하지 않는다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다. `STATUS.md` 갱신은 code diff ownership / single-writer 집계 대상에서 제외한다.
- 기본 실행 단위는 다음 slice 1개다.
- slice 실행 순서는 `writer edit -> main focused validation -> same writer commit-only -> STATUS update -> next slice decision`이다.
- phase 1은 fresh writer edit-only다.
- phase 2 focused validation은 메인 스레드가 수행한다.
- phase 3은 phase 1을 수행한 same writer가 commit-only로 재개한다.
- verification-worker는 메인 검증 로그가 noisy/multi-step일 때만 사용한다.
- focused validation이 실패하면 해당 slice는 커밋하지 않고 즉시 중단한다.
- 각 slice는 커밋을 정확히 1회 남겨야 하며, 커밋 메시지는 한국어 conventional commit 한 줄을 사용한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 slice 실패로 기록하고 다음 slice로 넘어가지 않는다.
- `fork_context` 기본값은 `false`다. 축약 불가능한 컨텍스트 의존일 때만 `true`를 허용하고 이유를 `STATUS.md`에 기록한다.
- slice hard guardrail: `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice로 묶는 giant mixed slice를 금지한다.
- full-repo validation은 shared/public boundary 변경 시에만 허용한다.
- 멀티에이전트 생명주기 경계는 `inactivity window`, `blocking deadline`, `drain grace`다. raw second(예: 90초/60초)를 정책 문구로 고정하지 않는다.
- stall 판정은 `communication liveness`와 `execution liveness`가 모두 끊겼을 때만 허용한다.
- close 절차는 `liveness 확인 -> interrupt로 final/checkpoint flush 요청 -> drain grace 대기 -> 결과 ACK -> close_agent` 순서를 따른다.
- `wait timeout = 즉시 실패/즉시 close`는 금지한다.
- worker 실패는 `상태: blocked`이거나 dual-signal inactivity 이후 drain grace 안에 `final/checkpoint`를 받지 못했을 때만 기록한다.
- advisory reviewer 미응답은 slice 실패로 처리하지 않고 background/advisory로 전환한다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 취급하고 그 외에는 advisory로 취급한다.
- 같은 slice에 두 번째 writer를 투입하지 않는다.
- partial diff는 오케스트레이터가 read-only inspection만 수행하고 `STATUS.md`에 기록한 뒤 재설계한다.

## Task Selection Rules

1. 사용자 지정 slug/path가 있으면 해당 task를 사용한다.
2. 지정이 없고 `tasks/` 아래 작업이 1개면 자동 선택한다.
3. 작업이 여러 개면 미완료 `Next slice`가 있는 task만 후보로 본다.
4. 후보가 정확히 1개면 자동 선택한다.
5. 후보가 2개 이상이면 사용자에게 task를 확인받는다.
6. 후보가 없으면 최근 수정 task를 참고하되 사용자 확인 전까지 실행하지 않는다.

## Mode Rules

- 사용자가 `계속해`라고 하면 현재 task의 다음 slice 1개를 수행한다.
- 사용자가 `끝까지` 또는 `stop condition 만날 때까지`를 명시하면 연속 실행 루프를 사용한다.
- 연속 실행 루프는 slice마다 새로운 `worker`를 phase 1에 배정한다.
- 각 slice의 phase 3 commit-only는 반드시 해당 slice phase 1을 수행한 same writer가 수행한다.
- 연속 실행 중 아래 조건이면 즉시 중단하고 `STATUS.md`만 갱신한다.
  - 검증 실패(커밋 시도 없음)
  - 커밋 실패(`--no-verify` 재시도 실패 포함)
  - worker가 `상태: blocked`를 보고
  - dual-signal inactivity 이후 `blocking deadline + drain grace` 안에 `final/checkpoint` 미수신
  - `PLAN.md`의 stop/replan 조건 충족
  - public boundary drift 발생
  - 다음 slice 진행 전 의사결정 공백 발생

## Execution Workflow

1. 대상 task를 선택한다.
2. `PLAN.md`에서 다음 미완료 slice와 검증 기준을 읽는다.
3. `STATUS.md`가 없으면 고정 템플릿 섹션으로 파일을 생성한다.
4. 현재 slice 기준 handoff brief를 만든다. brief에는 목표, 완료 기준, 변경 경계, 우선 확인 파일, phase, file budget, validation owner, fork_context policy, `blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`, commit requirement/timing/fallback policy를 포함한다.
5. phase 1: 현재 slice 전용 fresh `worker` 1명을 `fork_context:false` 기본값으로 spawn해 edit-only를 수행한다.
6. phase 1 진행 중 `inactivity window`에서 dual-signal liveness가 모두 끊기면 interrupt로 `final/checkpoint` flush를 요청한다.
7. `blocking deadline` 내 `final/checkpoint`가 없으면 `drain grace`로 전환한다. `drain grace` 내에도 결과가 없으면 slice 실패를 기록하고, partial diff를 read-only inspection 후 `STATUS.md`에 남기고 stop/replan한다.
8. `final/checkpoint`를 수신하면 오케스트레이터는 ACK를 기록한 뒤 phase 2로 진행한다.
9. phase 2: 메인 스레드가 focused validation을 실행한다. 기본값은 `타깃 검증 1개 + 저비용 체크 1개`다.
10. 검증 출력이 noisy하면 `verification-worker`가 메인 검증 로그를 해석하고 pass/fail을 요약한다. commit sign-off가 불가능한 경우에만 일시적으로 semi-blocking으로 취급한다.
11. focused validation이 실패하면 커밋하지 않고 slice 실패를 기록한다.
12. phase 3: focused validation이 통과한 경우에만 phase 1 same writer를 재개해 commit-only를 수행한다.
13. 1차 `git commit`이 hook 실패로 막히면 same writer는 동일 메시지로 `git commit --no-verify`를 1회만 재시도한다.
14. 커밋이 실패하면 오케스트레이터는 slice 실패를 기록하고 다음 slice로 진행하지 않는다.
15. 오케스트레이터는 worker/verifier의 요약만 받아 결과를 통합한다. 오케스트레이터는 raw log를 직접 처리하지 않는다.
16. 오케스트레이터가 `STATUS.md`를 manager-facing 요약으로 갱신한다.
17. `계속해` 모드면 종료한다. `끝까지` 모드면 다음 slice를 다시 읽고 4번부터 반복한다.

## Default Validation Fallback (Repo-Aware)

- `PLAN.md`에 검증 명령이 있으면 해당 명령을 우선 사용한다.
- `PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.
- focused validation owner는 메인 스레드다.
- 기본 focused validation은 `타깃 검증 1개 + 저비용 체크 1개`를 사용한다.
- full-repo validation은 shared/public boundary 변경으로 범위 확장이 필요한 경우에만 사용한다.
- JS/TS repo 추론: `package.json` + lockfile(`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`)를 기준으로 package manager를 고른다.
- Python repo 추론: `pyproject.toml` 또는 `tests/`/`test_*.py`를 기준으로 `python3 -m unittest discover`를 후보로 본다.
- 추론된 manager/도구에서 존재하는 스크립트(예: `typecheck`, `lint`, `test`)만 실행한다.
- 안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.

## Lane and Agent Rules

- 이 스킬은 lane 판정을 delegated team lane으로 고정한다.
- single-writer 적용 단위는 slice다. slice당 정확히 한 명의 `worker`만 code diff를 적용한다.
- 연속 실행 시에도 매 slice마다 새로운 `worker`를 phase 1에 사용하고, phase 3은 same writer commit-only를 유지한다.
- 오케스트레이터는 slice 선택, brief 작성, phase 2 focused validation 실행, stop/replan 판정, 상태 기록을 수행한다.
- handoff brief에는 `blocking_class`, `result_contract`, `close_protocol`, `liveness_signals`를 반드시 포함한다.
- writer 기본 동작은 edit-only이며 validation/commit은 handoff에 phase가 명시된 경우만 수행한다.
- 같은 slice에 두 번째 writer를 투입하지 않는다.
- 오케스트레이터의 `STATUS.md` 갱신은 메타 상태 기록이며 code diff ownership / single-writer 집계 대상에서 제외한다.
- noisy validation일 때만 `verification-worker`를 사용하고, 메인 검증 raw log 해석은 verifier가 담당한다.
- `fork_context` 기본값은 `false`이며 `true`는 축약 불가능한 컨텍스트 의존일 때만 허용한다.
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
- `# Decisions made during implementation`: 다음 slice 또는 공개 경계에 영향을 주는 의사결정만 적는다.
- `# Verification results`: 검증 명령, pass/fail, 커밋 시도 결과(기본 커밋/`--no-verify` 재시도 여부), 핵심 실패 원인만 적는다. raw log를 붙이지 않는다.
- `# Known issues / residual risk`: 남은 위험과 미해결 이슈를 적는다.
- `# Next slice`: 다음 writer가 바로 실행할 수 있도록 목표, 선행조건, 먼저 볼 경계를 handoff brief 형태로 적는다.
- `STATUS.md`를 최초 생성한 실행에서는 템플릿 생성 사실을 `# Done` 또는 `# Decisions made during implementation`에 기록한다.
- `fork_context:true`를 사용한 경우 이유를 `# Decisions made during implementation`에 기록한다.
- `inactivity window`/`blocking deadline`/`drain grace` 경로 또는 partial diff 발생 시 경과와 stop/replan 이유를 `# Verification results` 또는 `# Known issues / residual risk`에 기록한다.

## Non-Goals

- 레거시 문서/흐름 호환 로직을 추가하지 않는다.
- 실행 범위를 벗어난 임의 확장을 하지 않는다.
