# Working In This Repo

이 문서는 이 레포에서 작업하는 AI 에이전트와 유지보수자를 위한 작업 안내서다.
핵심은 "generated 파일을 직접 고치지 말고, source of truth만 수정한 뒤 projection을 재생성한다"는 것이다.

## Source Of Truth

| 변경 대상 | 실제 수정 위치 | 직접 수정 금지 |
|-----------|----------------|----------------|
| 에이전트 정의 | `agent-registry/<agent-id>/agent.toml`, `agent-registry/<agent-id>/instructions.md` | `agents/*.md`, `dist/codex/agents/*.toml`, `dist/codex/config.managed-agents.toml` |
| 글로벌 정책 | `INSTRUCTIONS.md` | `AGENTS.md`, `CLAUDE.md` |
| 스킬 | `skills/<skill-name>/...` | 설치된 `~/.claude/skills`, `~/.codex/skills` |

## Do Not Edit Directly

- `agents/*.md`
- `dist/codex/agents/*.toml`
- `dist/codex/config.managed-agents.toml`
- `AGENTS.md`
- `CLAUDE.md`

위 파일들은 생성물이므로 직접 수정하면 다음 sync에서 덮어써진다.

## Common Workflows

### 1. 에이전트 추가/수정

1. `agent-registry/<agent-id>/agent.toml`을 수정한다.
2. `agent-registry/<agent-id>/instructions.md`를 수정한다.
3. `python3 scripts/sync_agents.py`
4. `python3 scripts/sync_agents.py --check`
5. 실제 설치가 필요하면 `python3 scripts/install_assets.py --target all --link`

주의:

- `id`, `codex.agent_key`, `codex.config_file`는 충돌하면 안 된다.
- 현재는 `scripts/sync_agents.py --check`가 중복 충돌을 hard fail로 막는다.
- built-in Codex agent는 registry에 있어도 managed config에는 다시 쓰지 않는다.
- long-running task public surface는 `design-task`, `implement-task`만 유지한다.
- planning role은 internal fan-out 전용이며 user-facing install/projection 대상에서 제외한다.

### 2. 글로벌 정책 수정

1. `INSTRUCTIONS.md`를 수정한다.
2. `python3 scripts/sync_instructions.py`
3. `python3 scripts/sync_instructions.py --check`

`AGENTS.md`, `CLAUDE.md`는 projection이므로 직접 수정하지 않는다.

### 3. 스킬 수정

1. `skills/<skill-name>/SKILL.md` 또는 내부 `scripts/`, `references/`, `agents/`를 수정한다.
2. 스킬이 다른 source of truth를 참조하면 그 source를 먼저 갱신한다.
3. 관련 검증을 실행한다.

예:

- `design-task` 변경 시 planning role, role card, agent prompt를 함께 확인
- 설치 동작 변경 시 `install_assets.py --dry-run`으로 Claude/Codex 모두 확인

## Standard Validation

일반적으로 아래 순서면 충분하다.

```bash
python3 scripts/sync_instructions.py --check
python3 scripts/sync_agents.py --check
python3 scripts/validate_workflow_contracts.py
python3 scripts/install_assets.py --dry-run --target all
python3 -m unittest discover -s tests -p 'test_*.py'
```

설치 로직을 건드렸다면 추가로 확인한다.

```bash
python3 - <<'PY'
from pathlib import Path
import tomllib
config = Path.home() / ".codex" / "config.toml"
tomllib.loads(config.read_text(encoding="utf-8"))
print("codex config parse ok")
PY
```

## Installation Notes

- 실제 설치 진입점은 `python3 scripts/install_assets.py`다.
- legacy wrapper는 유지되지만 기준 구현은 Python이다.
- `--link`가 기본 권장 모드다.
- `--dry-run`으로 먼저 확인하는 편이 안전하다.

예:

```bash
python3 scripts/install_assets.py --target claude --link
python3 scripts/install_assets.py --target codex --link
python3 scripts/install_assets.py --target all --dry-run
```

## Repo-Specific Gotchas

- `agents/*.md`가 source처럼 보여도 이제는 projection이다.
- `dist/codex/config.managed-agents.toml`은 `~/.codex/config.toml`의 managed block으로만 들어간다.
- install 단계에서는 generated marker가 있는 agent 파일만 prune한다.
- skill은 generated manifest 기반으로 stale 항목만 prune한다(수동 디렉터리 보존).
- broken symlink도 install 단계에서 정리된다.
- `codex` 대상 설치는 helper built-in preflight를 통과해야 진행된다.
- `design-task`는 planning role을 직접 또는 fallback overlay로 사용한다. planning role을 바꾸면 `skills/design-task/SKILL.md`와 `skills/design-task/references/`도 같이 확인한다.

## When Unsure

다음 우선순위로 판단한다.

1. source of truth를 찾는다.
2. generated projection은 재생성으로 해결한다.
3. 설치 문제는 `--dry-run`과 Codex config parse로 먼저 확인한다.
4. 그래도 모호하면 `README.md`, `INSTRUCTIONS.md`, 이 문서를 다시 확인한다.
