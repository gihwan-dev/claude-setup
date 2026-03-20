# Working In This Repo

핵심 규칙은 단순하다. generated 파일은 직접 수정하지 않고, source of truth를 고친 뒤 sync와 check를 돌린다.

## Pick The Right Source

| 작업 | 수정 위치 | 직접 수정 금지 |
|------|-----------|----------------|
| agent 수정 | `agent-registry/<agent-id>/agent.toml`, `agent-registry/<agent-id>/instructions.md` | `agents/*.md`, `dist/codex/agents/*.toml`, `dist/codex/config.managed-agents.toml` |
| skill 수정 | `skills/<skill-name>/...` | `skills/INDEX.md`, `skills/manifest.json`, 설치된 `~/.claude/skills`, `~/.codex/skills` |

`skills/`가 canonical source다. `.agents/skills`는 기본 source가 아니라 설치 호환을 위한 legacy overlay로만 취급한다.

## Runbook

### agent 수정

1. `agent-registry/<agent-id>/agent.toml`을 수정한다.
2. `agent-registry/<agent-id>/instructions.md`를 수정한다.
3. `python3 scripts/sync_agents.py`
4. `python3 scripts/sync_agents.py --check`

### skill 수정

1. `skills/<skill-name>/SKILL.md` 또는 내부 `scripts/`, `references/`, `agents/`를 수정한다.
2. `python3 scripts/sync_skills_index.py`
3. `python3 scripts/sync_skills_index.py --check`
4. 스킬이 다른 source를 참조하면 그 source를 먼저 갱신한다.
5. 관련 검증을 실행한다.

## Standard Validation

보통 아래 순서면 충분하다.

```bash
python3 scripts/sync_agents.py --check
python3 scripts/sync_skills_index.py --check
python3 scripts/validate_workflow_contracts.py
python3 scripts/install_assets.py --dry-run --target all
python3 -m unittest discover -s tests -p 'test_*.py'
```

설치 로직을 건드렸다면 실제 설정 파일도 파싱해 본다.

```bash
python3 - <<'PY'
from pathlib import Path
import tomllib
config = Path.home() / ".codex" / "config.toml"
tomllib.loads(config.read_text(encoding="utf-8"))
print("codex config parse ok")
PY
```

## Git Hooks (Primary)

처음 clone하면 hook을 활성화한다:

    bash scripts/setup-hooks.sh

이후 commit, merge, branch switch 시 관련 파일이 바뀌면 `install_assets.py --link`가 자동 실행된다.

- 비활성화: `git config --unset core.hooksPath`
- 에러가 발생해도 git 동작은 차단하지 않는다 (경고만 출력).

## Manual Install (초기 세팅 / 트러블슈팅)

hooks가 활성화되어 있으면 수동 설치는 보통 불필요하다.

- 기준 진입점: `python3 scripts/install_assets.py`
- `--link`가 기본 권장 모드다.
- linked git worktree에서는 설치 mode가 자동으로 `copy`로 강등된다.
- 설치는 항상 canonical source인 `skills/`를 먼저 반영한다.
- `.agents/skills`가 존재하면 legacy overlay로 추가 설치된다.
- generated drift를 먼저 해소한 뒤 설치한다.
- repo-managed legacy global rule markdown은 설치하지 않고 stale top-level rule files만 안전하게 prune한다.

## When Unsure

1. 어떤 파일이 source of truth인지 먼저 확인한다.
2. generated 파일은 재생성으로 맞춘다.
3. 설치 문제는 `--dry-run`으로 먼저 확인한다.
4. 그래도 모호하면 [README.md](./README.md), 관련 `skills/`, `agent-registry/`를 다시 읽는다.
