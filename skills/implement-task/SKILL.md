---
name: implement-task
description: >
  Implementation execution skill for long-running tasks. Use when the user says "구현해줘",
  "다음 단계 진행해", "계속해", or asks to execute based on an existing design.
  Read tasks/{task-slug}/PLAN.md, execute the next slice, and always update tasks/{task-slug}/STATUS.md.
---

# Workflow: Implement Task

## Goal

`tasks/<task-slug>/PLAN.md` 기준으로 실행 슬라이스를 구현하고 `STATUS.md`를 갱신한다.

## Hard Rules

- 항상 `PLAN.md`와 기존 `STATUS.md`를 먼저 읽는다.
- `PLAN.md`가 없으면 구현하지 않고 `design-task`를 먼저 수행하도록 유도한다.
- 이 스킬은 승인된 `PLAN.md` 기반 long-running 실행만 다룬다.
- 기존 코드 구현은 `PLAN.md` 없이 즉시 시작하지 않는다.
- `STATUS.md`가 없으면 고정 템플릿 섹션으로 `tasks/<task-slug>/STATUS.md`를 먼저 생성한 뒤 실행 기록을 채운다.
- `implement-task`의 code writer는 메인 스레드 하나다.
- `implement-task`는 writable sub-agent를 사용하지 않는다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 기본 실행 단위는 다음 slice 1개다.
- focused validation은 메인 스레드가 수행한다.
- verification-worker는 메인 검증 로그가 noisy/multi-step일 때만 사용한다.
- focused validation이 실패하면 해당 slice는 커밋하지 않고 즉시 중단한다.
- 각 slice는 커밋을 정확히 1회 남겨야 하며, 커밋 메시지는 한국어 conventional commit 한 줄을 사용한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 slice 실패로 기록하고 다음 slice로 넘어가지 않는다.
- slice hard guardrail: `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`, 순 diff `150 LOC 내외`.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice로 묶는 giant mixed slice를 금지한다.
- full-repo validation은 shared/public boundary 변경 시에만 허용한다.
- advisory reviewer 미응답은 slice 실패로 처리하지 않고 background/advisory로 전환한다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 취급하고 그 외에는 advisory로 취급한다.
- 리뷰 요청에서 구조 개선 계획을 새로 만드는 역할은 이 스킬이 아니라 `design-task`/reviewer에 있다. `implement-task`는 승인된 계획 실행에만 집중한다.

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
4. 메인 스레드가 현재 slice의 코드 변경을 직접 수행한다.
5. 메인 스레드가 focused validation을 실행한다. 기본값은 `타깃 검증 1개 + 저비용 체크 1개`다.
6. 검증 출력이 noisy하면 `verification-worker`가 메인 검증 로그를 해석하고 pass/fail을 요약한다. commit sign-off가 불가능한 경우에만 일시적으로 semi-blocking으로 취급한다.
7. focused validation이 실패하면 커밋하지 않고 slice 실패를 기록한다.
8. focused validation이 통과하면 커밋한다.
9. 1차 `git commit`이 hook 실패로 막히면 동일 메시지로 `git commit --no-verify`를 1회만 재시도한다.
10. 커밋이 실패하면 slice 실패를 기록하고 다음 slice로 진행하지 않는다.
11. `STATUS.md`를 manager-facing 요약으로 갱신한다.
12. `계속해` 모드면 종료한다. `끝까지` 모드면 다음 slice를 다시 읽고 4번부터 반복한다.

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

- `implement-task`의 code writer는 메인 스레드 하나다.
- `implement-task`는 writable sub-agent를 사용하지 않는다.
- 오케스트레이터는 slice 선택, focused validation 실행, stop/replan 판정, 상태 기록을 수행한다.
- read-only helper fan-out은 탐색/리뷰/로그 해석이 필요할 때만 사용한다.
- noisy validation일 때만 `verification-worker`를 사용하고, 메인 검증 raw log 해석은 verifier가 담당한다.
- `module-structure-gatekeeper`는 비trivial code diff 이후 자동 reviewer로 실행한다.
- `frontend-structure-gatekeeper`는 비trivial frontend diff에서 추가 자동 reviewer로 실행한다.
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
- `# Next slice`: 바로 실행할 수 있도록 목표, 선행조건, 먼저 볼 경계를 적는다.
- `STATUS.md`를 최초 생성한 실행에서는 템플릿 생성 사실을 `# Done` 또는 `# Decisions made during implementation`에 기록한다.

## Non-Goals

- 레거시 문서/흐름 호환 로직을 추가하지 않는다.
- 실행 범위를 벗어난 임의 확장을 하지 않는다.
