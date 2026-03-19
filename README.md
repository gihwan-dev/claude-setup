# AI Agent SSOT Repo

Claude Code, Codex 등 여러 에이전트 도구에 공통으로 설치할 정책, agent registry, skill source를 관리하는 저장소다.

처음 작업할 때는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 읽는다.

## What Lives Here

- 정책 source: `docs/policy/*.md`
- agent source: `agent-registry/<agent-id>/...`
- skill source: `skills/<skill-name>/...`
- generated 파일은 직접 수정하지 않는다.

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

## Working Here

- 수정/검증/설치 절차는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 기준으로 본다.
- 세부 오케스트레이션 규칙은 [`docs/policy/`](docs/policy/)를 기준으로 본다.
- Codex/Claude projection은 source 수정 후 sync로 재생성한다.
