---
name: implement-task
description: >
  Implementation execution skill for long-running tasks. Use when the user says "구현해줘",
  "다음 단계 진행해", "계속해", or asks to execute based on an existing design.
  Read tasks/{task-slug}/PLAN.md, execute the next slice, and always update tasks/{task-slug}/STATUS.md.
---

# Workflow: Implement Task

## Goal

`tasks/<task-slug>/PLAN.md` 기준으로 실행 슬라이스를 구현하고, 오케스트레이터가 `STATUS.md`를 단일 상태 문서로 갱신한다.

## Hard Rules

- 항상 `PLAN.md`와 기존 `STATUS.md`를 먼저 읽는다.
- `PLAN.md`가 없으면 구현하지 않고 `design-task`를 먼저 수행하도록 유도한다.
- `STATUS.md`가 없으면 고정 템플릿 섹션으로 `tasks/<task-slug>/STATUS.md`를 먼저 생성한 뒤 실행 기록을 채운다.
- `implement-task`는 항상 delegated lane으로 실행한다. fast lane/deep solo를 이 스킬에서 허용하지 않는다.
- 코드 수정은 `worker`만 수행한다. 오케스트레이터는 코드 수정을 수행하지 않는다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다. `STATUS.md` 갱신은 code diff ownership / single-writer 집계 대상에서 제외한다.
- 기본 실행 단위는 다음 slice 1개다.
- slice 실행 순서는 `구현 -> focused validation -> slice commit -> STATUS 갱신`이다.
- focused validation이 실패하면 해당 slice는 커밋하지 않고 즉시 중단한다.
- 각 slice는 커밋을 정확히 1회 남겨야 하며, 커밋 메시지는 한국어 conventional commit 한 줄을 사용한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 slice 실패로 기록하고 다음 slice로 넘어가지 않는다.

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
- 연속 실행 루프는 slice마다 새로운 `worker`를 사용한다. 이전 writer session 재사용은 금지한다.
- `끝까지` 모드에서 여러 fresh `worker`가 순차 참여해도 slice당 single-writer를 만족하면 규칙 위반이 아니다.
- 연속 실행 중 아래 조건이면 즉시 중단하고 `STATUS.md`만 갱신한다.
  - 검증 실패(커밋 시도 없음)
  - 커밋 실패(`--no-verify` 재시도 실패 포함)
  - `PLAN.md`의 stop/replan 조건 충족
  - public boundary drift 발생
  - 다음 slice 진행 전 의사결정 공백 발생

## Execution Workflow

1. 대상 task를 선택한다.
2. `PLAN.md`에서 다음 미완료 slice와 검증 기준을 읽는다.
3. `STATUS.md`가 없으면 고정 템플릿 섹션으로 파일을 생성한다.
4. 현재 slice 기준 handoff brief를 만든다. brief에는 목표, 완료 기준, 변경 경계, 우선 확인 파일, 검증 기준, commit requirement/timing/fallback policy를 최소 정보로 포함한다.
5. 현재 slice 전용 fresh `worker` 1명을 spawn한다.
6. `worker`가 현재 slice 구현과 focused validation을 수행한다. `PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.
7. 검증 출력이 noisy하면 `verification-worker`가 raw log를 해석하고 pass/fail을 요약한다.
8. focused validation이 통과한 경우에만 `worker`가 해당 slice 변경을 커밋한다. 커밋 메시지는 한국어 conventional commit 한 줄을 사용한다.
9. 1차 `git commit`이 hook 실패로 막히면 `worker`는 동일 메시지로 `git commit --no-verify`를 1회만 재시도한다.
10. 커밋이 실패하면 오케스트레이터는 slice 실패를 기록하고 다음 slice로 진행하지 않는다.
11. 오케스트레이터는 worker/verifier의 요약만 받아 결과를 통합한다. 오케스트레이터는 raw log를 직접 처리하지 않는다.
12. 오케스트레이터가 `STATUS.md`를 manager-facing 요약으로 갱신한다.
13. `계속해` 모드면 종료한다. `끝까지` 모드면 다음 slice를 다시 읽고 4번부터 반복한다.

## Default Validation Fallback (Repo-Aware)

- `PLAN.md`에 검증 명령이 있으면 해당 명령을 우선 사용한다.
- `PLAN.md` 검증이 비어 있을 때만 repo-aware fallback을 사용한다.
- JS/TS repo 추론: `package.json` + lockfile(`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`)를 기준으로 package manager를 고른다.
- Python repo 추론: `pyproject.toml` 또는 `tests/`/`test_*.py`를 기준으로 `python3 -m unittest discover`를 후보로 본다.
- 추론된 manager/도구에서 존재하는 스크립트(예: `typecheck`, `lint`, `test`)만 실행한다.
- 안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.

## Lane and Agent Rules

- 이 스킬은 lane 판정을 delegated team lane으로 고정한다.
- single-writer 적용 단위는 slice다. slice당 정확히 한 명의 `worker`만 code diff를 적용한다.
- 연속 실행 시에도 매 slice마다 새로운 `worker`를 사용한다.
- 오케스트레이터는 slice 선택, brief 작성, stop/replan 판정, 상태 기록만 수행한다.
- writer는 slice별 `구현 -> 검증 -> 커밋`을 수행하고, 오케스트레이터는 커밋 결과를 반영해 상태를 기록한다.
- 오케스트레이터의 `STATUS.md` 갱신은 메타 상태 기록이며 code diff ownership / single-writer 집계 대상에서 제외한다.
- noisy validation일 때만 `verification-worker`를 사용하고, raw log 해석은 verifier가 담당한다.
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

## Non-Goals

- 레거시 문서/흐름 호환 로직을 추가하지 않는다.
- 실행 범위를 벗어난 임의 확장을 하지 않는다.
