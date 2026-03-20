# AI Agent SSOT Repo

Claude Code, Codex 등 여러 에이전트 도구에 공통으로 설치할 agent registry와 skill source를 관리하는 저장소다.

처음 작업할 때는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 읽는다.

## What Lives Here

- agent source: `agent-registry/<agent-id>/...`
- skill source: `skills/<skill-name>/...`
- generated projection은 직접 수정하지 않는다.

## Repo Map

```text
agent-registry/<agent-id>/...                 # agent SSOT
skills/<skill-name>/...                       # skill SSOT
scripts/sync_agents.py                        # agent-registry -> generated projections
scripts/sync_skills_index.py                  # skills/*/SKILL.md -> skills/INDEX.md, skills/manifest.json
scripts/install_assets.py                     # Claude/Codex 설치 진입점
agents/*.md                                   # Claude projection
dist/codex/agents/*.toml                      # Codex projection
dist/codex/config.managed-agents.toml         # Codex managed config block
```

## Working Here

- 수정/검증/설치 절차는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 기준으로 본다.
- 설치는 skill/agent 자산만 다룬다.
- legacy global rule markdown은 더 이상 설치하지 않으며, repo-managed stale 파일만 정리한다.
