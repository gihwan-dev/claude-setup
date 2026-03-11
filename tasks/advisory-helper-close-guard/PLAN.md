# Goal

Advisory helper의 조기 종료를 막기 위해 helper spawn/close 판단을 machine-checkable contract로 바꾸고, Claude/Codex projection까지 동일 정책으로 동기화한다.

# Task Type

refactor

# Scope / Non-goals

- 포함:
  - helper `[orchestration]` schema에 `timeout_policy`, `allowed_close_reasons` 추가
  - advisory helper close preflight 정책과 spawn gate를 코드/문서/테스트로 고정
  - task/skill/agent instruction/source 문구 및 generated projection 동기화
  - validator와 회귀 테스트 확장
- 제외:
  - Codex/호스트 앱의 실제 `close_agent` 런타임 구현 변경
  - 제품 코드나 외부 애플리케이션 동작 수정

# Keep / Change / Don't touch

- Keep:
  - single-writer delegated flow
  - `worker` blocking, `verification-worker` semi-blocking 역할 구분
  - existing helper ids와 projection 구조
- Change:
  - advisory helper의 timeout/nonresponse 처리
  - advisory helper spawn 기본값(작은/저위험 slice에서는 fan-out 축소)
  - helper lifecycle contract를 validator/test가 직접 검증하도록 확장
- Don't touch:
  - host runtime close controller
  - unrelated install/skill behavior

# Evidence

## Repo evidence

- `INSTRUCTIONS.md`, `skills/implement-task/SKILL.md`는 이미 `wait timeout != stalled`, `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 규칙을 문서화하고 있다.
- `scripts/workflow_contract.py`와 `scripts/validate_workflow_contracts.py`는 기존에는 orchestration 메타데이터/문구 일치만 검증하고, advisory close/spawn 판단 함수는 제공하지 않았다.
- `tests/test_workflow_stability.py`는 문구/직렬화/managed config 드리프트 중심 테스트만 갖고 있고, `timed_out -> running -> close` 시퀀스를 직접 reject하는 테스트가 없었다.

## External evidence

- 없음. 이 작업은 repo-local SSOT와 generated projection 동기화 범위다.

## Options considered

- 문서/테스트만 강화: 실제 조기 close 금지 로직이 없어 제외
- host runtime까지 포함: 이 레포 범위를 넘어가므로 제외
- repo-local contract + validator/test 강화: 채택

# Decisions / Open questions

## Chosen approach

- quality preflight verdict는 `promote-architecture`로 고정한다.
- 모든 advisory helper(`explorer`, reviewer, gatekeeper)에 `timeout_policy = "background-no-close"`와 `allowed_close_reasons = ["explicit-cancel", "hard-deadline", "blocked"]`를 적용한다.
- `worker`, `verification-worker`는 기존 blocking class를 유지하되 `timeout_policy = "observe-and-status-ping"`와 동일 `allowed_close_reasons`를 사용한다.
- `scripts/workflow_contract.py`에 `decide_helper_close_action(snapshot)`, `should_spawn_advisory_helper(slice_context)`를 추가해 machine-checkable 규범으로 고정한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고, advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 수 있을 때만 허용한다.

## Rejected alternatives

- `result가 더 이상 필요 없음`을 close 근거로 인정하는 운영
- `wait timed_out -> status running -> no result -> close`를 허용하는 heuristic cleanup
- advisory helper를 reviewer에만 한정 적용하는 축소 버전

## Need user decision

- 없음

## Quality preflight

- verdict: `promote-architecture`
- 근거:
  - shared helper lifecycle policy와 실제 집행/검증 레이어가 분리돼 있음
  - 여러 source-of-truth, generated projection, tests를 동시에 수정해야 함
  - public/shared orchestration contract(`[orchestration]`)이 바뀜
- 후속 경로:
  - task 문서 생성 후 source-of-truth 수정
  - sync/generation
  - focused validation + drift checks

# Execution slices

## Slice 1

- Change boundary:
  - `tasks/advisory-helper-close-guard/PLAN.md`
  - `tasks/advisory-helper-close-guard/STATUS.md`
  - `scripts/workflow_contract.py`
  - `scripts/sync_agents.py`
- Expected files:
  - 4
- Validation owner:
  - main thread
- Focused validation plan:
  - `python3 scripts/sync_agents.py --check`
  - `python3 scripts/validate_workflow_contracts.py`
- Stop / Replan trigger:
  - orchestration schema 직렬화가 list 값을 보존하지 못할 때

## Slice 2

- Change boundary:
  - `INSTRUCTIONS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `skills/implement-task/SKILL.md`
  - `skills/implement-task/agents/openai.yaml`
  - `agent-registry/project-planner/instructions.md`
  - advisory helper 관련 `agent-registry/*/agent.toml`
  - advisory helper 관련 `agent-registry/*/instructions.md`
- Expected files:
  - 단일 helper-lifecycle policy boundary 예외
- Validation owner:
  - main thread
- Focused validation plan:
  - `python3 scripts/sync_instructions.py --check`
  - `python3 scripts/validate_workflow_contracts.py`
- Stop / Replan trigger:
  - source policy와 agent registry phrasing이 generated projection과 충돌할 때

## Slice 3

- Change boundary:
  - `tests/test_workflow_stability.py`
  - generated `AGENTS.md`, `CLAUDE.md`, `agents/*.md`, `dist/codex/**`
- Expected files:
  - generated/test boundary 예외
- Validation owner:
  - main thread
- Focused validation plan:
  - `python3 scripts/sync_instructions.py`
  - `python3 scripts/sync_agents.py`
  - `python3 scripts/sync_instructions.py --check`
  - `python3 scripts/sync_agents.py --check`
  - `python3 scripts/validate_workflow_contracts.py`
  - `python3 -m unittest tests/test_workflow_stability.py`
- Stop / Replan trigger:
  - bad sequence rejection, late result merge, spawn gate 시나리오 중 하나라도 테스트로 고정하지 못할 때

# Verification

- `python3 scripts/sync_instructions.py`
- `python3 scripts/sync_agents.py`
- `python3 scripts/sync_instructions.py --check`
- `python3 scripts/sync_agents.py --check`
- `python3 scripts/validate_workflow_contracts.py`
- `python3 -m unittest tests/test_workflow_stability.py`
- `git diff --check`

# Stop / Replan conditions

- advisory helper close preflight가 strong close reason 없이 `close`를 허용하면 중단한다.
- source policy와 generated projection phrasing이 어긋나 drift를 해소하지 못하면 중단한다.
- list형 `allowed_close_reasons`가 registry/serialization/validator/test 중 한 경로라도 손실되면 재설계한다.
