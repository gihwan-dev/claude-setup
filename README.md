# AI Agent SSOT Repo

Claude Code, Codex 등 여러 에이전트 도구에 공통으로 설치할 정책, agent registry, skill source를 관리하는 저장소다.

처음 작업할 때는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 읽는다.

## Source Of Truth

| 대상 | 실제 수정 위치 | 생성/설치 결과 |
|------|----------------|----------------|
| 정책 문서 | `docs/policy/*.md` | `INSTRUCTIONS.md`, `AGENTS.md`, `CLAUDE.md` |
| 에이전트 계약 | `agent-registry/<agent-id>/agent.toml`, `agent-registry/<agent-id>/instructions.md` | `agents/*.md`, `dist/codex/agents/*.toml`, `dist/codex/config.managed-agents.toml` |
| 스킬 | `skills/<skill-name>/...` | `skills/INDEX.md`, `skills/manifest.json`, 설치된 `~/.claude/skills`, `~/.codex/skills` |

`skills/`가 canonical source다. `.agents/skills`는 설치 호환을 위한 legacy overlay일 뿐 authoring source가 아니다.

## Repo Map

```text
docs/policy/                                  # 정책 authoring source
agent-registry/<agent-id>/...                 # agent SSOT
skills/<skill-name>/...                       # skill SSOT
scripts/sync_instructions.py                  # docs/policy -> INSTRUCTIONS/AGENTS/CLAUDE
scripts/sync_agents.py                        # agent-registry -> generated projections
scripts/sync_skills_index.py                 # skills/*/SKILL.md -> skills/INDEX.md, skills/manifest.json
scripts/install_assets.py                     # Claude/Codex 설치 진입점
INSTRUCTIONS.md                               # compiled source doc
AGENTS.md                                     # Codex projection
CLAUDE.md                                     # Claude wrapper
```

## Quickstart

정책이나 registry를 수정한 뒤에는 아래 순서로 재생성/검증한다.

```bash
python3 scripts/sync_instructions.py
python3 scripts/sync_agents.py
python3 scripts/sync_skills_index.py
python3 scripts/sync_instructions.py --check
python3 scripts/sync_agents.py --check
python3 scripts/sync_skills_index.py --check
python3 scripts/validate_workflow_contracts.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

설치 동작까지 확인하려면:

```bash
python3 scripts/install_assets.py --dry-run --target all
```

### Git Hooks (Primary)

처음 clone하면 hook을 활성화한다:

    bash scripts/setup-hooks.sh

이후 commit, merge, branch switch 시 관련 파일이 바뀌면 `install_assets.py --link`가 자동 실행된다.

linked git worktree에서는 설치가 자동으로 `copy`로 강등한다.

### Manual Install (초기 세팅)

```bash
python3 scripts/install_assets.py --target claude --link
python3 scripts/install_assets.py --target codex --link
```

## Notes

- generated 파일은 직접 수정하지 않는다.
- shell wrapper는 legacy 호환용이고 기준 구현은 Python 스크립트다.
- skill index/manifest는 `python3 scripts/sync_skills_index.py`로 갱신한다.
- 설치 시에는 `skills/`를 먼저 반영하고, `.agents/skills`가 존재하면 legacy overlay로 덮어쓴다.
- 세부 정책은 [`docs/policy/`](docs/policy/)와 [CONTRIBUTING.md](./CONTRIBUTING.md)에 정리한다.
