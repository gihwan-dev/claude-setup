# AI Agent Skills

AI 에이전트(Claude Code, Codex 등)를 위한 스킬/에이전트 레지스트리 저장소다.

처음 작업할 때는 [CONTRIBUTING.md](/Users/choegihwan/Documents/Projects/claude-setup/CONTRIBUTING.md)를 먼저 읽는 것을 권장한다.
이 문서에는 수정해야 할 source of truth, 생성물 재생성, 설치/검증 절차가 정리되어 있다.

## 구조

```text
skills/<skill-name>/...                         # 스킬 정의/스크립트/레퍼런스
agent-registry/<agent-id>/agent.toml           # 에이전트 단일 진실원 메타데이터
agent-registry/<agent-id>/instructions.md      # 에이전트 단일 진실원 지시문
agents/*.md                                    # generated projection (수정 금지)
dist/codex/agents/*.toml                       # generated codex agent profiles
dist/codex/config.managed-agents.toml          # generated codex managed config block
scripts/sync_instructions.py                   # INSTRUCTIONS.md -> AGENTS.md/CLAUDE.md
scripts/sync_agents.py                         # agent-registry -> generated projections
scripts/install_assets.py                      # 설치/동기화 통합 진입점
scripts/install-skills.sh                      # legacy wrapper (install_assets.py 호출)
scripts/sync-instructions.sh                   # legacy wrapper (sync_instructions.py 호출)
INSTRUCTIONS.md                                # 프로젝트 정책 단일 소스
CLAUDE.md / AGENTS.md                          # generated files
```

## 단일 진실원 정책

- 에이전트: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- core helper 생명주기 정책: 각 helper `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)
- `agents/*.md`, `dist/codex/*`: generated projection
- 정책 문서: `INSTRUCTIONS.md`
- long-running task public surface: `design-task`, `implement-task`
- planning role은 internal fan-out 전용이며 user-facing install/projection 대상이 아니다.
- 설치되는 agent projection에서 writable 예외는 `worker` 하나뿐이다. 나머지 generated agent는 read-only helper/reviewer만 유지한다.
- `monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection을 만들지 않는다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.
- advisory helper close preflight에서는 `result가 더 이상 필요 없음`과 `wait timed_out -> status running -> no result -> close`를 종료 근거로 인정하지 않는다.

## 작업 시작 전

- generated projection을 직접 수정하지 않는다.
- 먼저 어떤 파일이 source of truth인지 결정한다.
- source-of-truth 수정 후에는 `python3 scripts/sync_instructions.py`, `python3 scripts/sync_agents.py` 순서로 projection을 재생성한다.
- 작업 후에는 `sync`와 `--check`를 실행해 drift가 없는지 확인한다.
- 실제 홈 디렉터리 설치가 필요하면 마지막에 `install_assets.py`를 실행한다.

빠른 작업 가이드:

| 작업 | 수정 위치 | 후속 명령 |
|------|-----------|-----------|
| 에이전트 추가/수정 | `agent-registry/<agent-id>/...` | `python3 scripts/sync_agents.py` |
| 글로벌 정책 수정 | `INSTRUCTIONS.md` | `python3 scripts/sync_instructions.py` |
| 스킬 수정 | `skills/<skill-name>/...` | 필요 시 skill 자체 검증 |
| 로컬 설치 반영 | source 수정 후 | `python3 scripts/install_assets.py --target all --link` |

## 동기화/검증

```bash
python3 scripts/sync_instructions.py
python3 scripts/sync_agents.py
```

drift 확인:

```bash
python3 scripts/sync_instructions.py --check
python3 scripts/sync_agents.py --check
python3 scripts/validate_workflow_contracts.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 설치 (Python-first)

자동 감지:

```bash
python3 scripts/install_assets.py --link
```

대상 지정:

```bash
python3 scripts/install_assets.py --target claude --link
python3 scripts/install_assets.py --target codex --link
python3 scripts/install_assets.py --target all --link
```

`codex` 설치 시에는 managed runtime agent preflight(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)를 먼저 확인하고 실패하면 중단한다.

옵션:

```text
--target <claude|codex|all>
--copy
--link
--dest <path>    # custom path (skills only)
--dry-run
```

## Legacy Wrapper

기존 명령도 동작한다.

```bash
./scripts/install-skills.sh --target codex --dry-run
./scripts/sync-instructions.sh --check
```

## 경로 규칙

| 변수 | 의미 | 용도 |
|------|------|------|
| `${SKILL_DIR}` | 현재 SKILL.md 위치 | 자체 scripts/references 참조 |
| `${SKILLS_ROOT}` | 스킬 루트 디렉토리 | 다른 스킬 참조 |
