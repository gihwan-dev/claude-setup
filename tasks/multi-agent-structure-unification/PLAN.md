# Goal

멀티 에이전트 구조 리뷰를 프런트엔드 전용에서 공통 코드 전체로 확장하고, Codex agent 등록/설치를 repo managed block 단일 경로로 일원화한다.

# Task Type

refactor

# Scope / Non-goals

- 포함:
  - 공통 구조 reviewer(`module-structure-gatekeeper`) 추가
  - `structure-planner`를 공통 모듈 분해 planner로 일반화
  - Codex managed config 생성 시 helper 전체 포함
  - legacy top-level helper config를 managed block으로 마이그레이션
  - 정책/skills/generated 문서 동기화
- 제외:
  - 기존 agent id 변경
  - unrelated skill/workflow redesign
  - 실제 제품 코드 리팩터링

# Keep / Change / Don't touch

- Keep:
  - `frontend-structure-gatekeeper` id와 React 특화 리뷰 역할
  - `code-reviewer`, `code-quality-reviewer`의 일반 품질 리뷰 역할
- Change:
  - 구조 비대화/책임 분리 제동 책임을 gatekeeper 계열로 분리
  - managed block가 helper 등록의 SSOT가 되도록 생성/설치 경로 변경
- Don't touch:
  - planning-role의 internal-only projection 원칙
  - single-writer / slice / validation lifecycle 계약

# Evidence

- `scripts/sync_agents.py`는 managed config 생성 시 `source != "codex-builtin"` 조건으로 builtin helper를 제외하고 있다.
- `~/.codex/config.toml`에는 helper 일부가 top-level `[agents.*]` 로 남고, repo managed block에는 repo-agent 위주만 들어가 있어 혼합 상태다.
- `frontend-structure-gatekeeper`와 `structure-planner` 설명/트리거는 현재 프런트엔드 전용이다.
- `scripts/workflow_contract.py`와 `scripts/validate_workflow_contracts.py`는 helper 존재/오케스트레이션만 검증하고 generated managed config helper 포함 여부는 직접 검증하지 않는다.

# Decisions / Open questions

- 결정:
  - 공통 구조 reviewer는 새 `module-structure-gatekeeper`로 추가한다.
  - `frontend-structure-gatekeeper`는 React 특화 gate로 유지한다.
  - hard FAIL은 구조 위반에만 적용하고, soft limit 초과는 advisory로 남긴다.
  - managed config는 source 구분 없이 `codex=true` agent 전체를 포함한다.
  - legacy helper top-level tables는 installer가 제거/정리한다.
- Open questions:
  - 없음. 사용자 승인 계획을 그대로 적용한다.

# Execution slices

## Slice 1

- 목표:
  - 공통 구조 gatekeeper 추가
  - `structure-planner` 일반화
  - 정책/skill/orchestration 문구를 공통 구조 리뷰 기준으로 갱신
- 변경 경계:
  - `policy/workflow.toml`
  - `scripts/workflow_contract.py`
  - `skills/design-task/SKILL.md`
  - `skills/design-task/references/planning-role-cards.md`
  - `skills/implement-task/SKILL.md`
  - `agent-registry/project-planner/instructions.md`
  - `agent-registry/structure-planner/*`
  - `agent-registry/frontend-structure-gatekeeper/*`
  - `agent-registry/module-structure-gatekeeper/*`
- 예상 파일 수:
  - 모듈 경계 예외. 단일 orchestration/policy boundary 내 다수 파일.
- validation owner:
  - main thread
- stop/replan 조건:
  - helper 계약 문구와 workflow validation을 동시에 만족시키지 못할 때

## Slice 2

- 목표:
  - sync/install/validation 경로를 managed SSOT 기준으로 통일
  - legacy helper config migration 추가
  - required helper 목록에 `module-structure-gatekeeper` 반영
- 변경 경계:
  - `scripts/sync_agents.py`
  - `scripts/install_assets.py`
  - `scripts/validate_workflow_contracts.py`
  - `scripts/workflow_contract.py`
- 예상 파일 수:
  - 4
- validation owner:
  - main thread
- stop/replan 조건:
  - 기존 Codex config에서 duplicate table 정리를 안전하게 할 수 없을 때

## Slice 3

- 목표:
  - generated artifacts 갱신
  - focused validation 및 install dry-run 확인
  - advisory review 반영
- 변경 경계:
  - generated helper projections under `dist/codex/**`, `agents/**`
- 예상 파일 수:
  - generated boundary 예외
- validation owner:
  - main thread
- stop/replan 조건:
  - sync/check 결과가 상충하거나 generated drift가 남을 때

# Verification

- `python3 scripts/sync_agents.py --check`
- `python3 scripts/validate_workflow_contracts.py`
- `python3 scripts/install_assets.py --target codex --dry-run`
- 필요 시 temporary legacy config fixture로 migration behavior 확인

# Stop / Replan conditions

- `module-structure-gatekeeper`를 helper 집합/managed config/installer validation 세 경로에 일관되게 반영하지 못하면 중단한다.
- legacy top-level helper cleanup이 기존 사용자 config의 unrelated section을 훼손할 위험이 있으면 정밀 migration으로 재설계한다.
- workflow contract 문구 변경이 generated helper output과 충돌하면 canonical source 기준으로 다시 정렬한다.
