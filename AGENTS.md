<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Run: python3 scripts/sync_instructions.py -->

# Repository Guidance

세부 정책은 `docs/policy/*.md`와 `CONTRIBUTING.md`를 본다.

## Core Goal

- 메인 스레드는 전략과 의사결정에 집중한다.
- 실행 작업은 필요한 경우에만 위임하고, 간결한 요약만 반환받는다.

## Source Of Truth

- 정책 authoring source: `docs/policy/*.md`
- agent contract: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- skill canonical source: `skills/`
- generated output: `INSTRUCTIONS.md`, `AGENTS.md`, `CLAUDE.md`, `skills/INDEX.md`, `skills/manifest.json`, `agents/*.md`, `dist/codex/*`

## Required Commands

```bash
python3 scripts/sync_instructions.py
python3 scripts/sync_agents.py
python3 scripts/sync_skills_index.py
python3 scripts/validate_workflow_contracts.py
python3 scripts/install_assets.py --dry-run --target all
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Important Constraints

- delegated lane에서 writer 위임은 조건부다. 메인 스레드가 기본 구현자이며, 대규모 변경 시 파일 경계가 명확한 작업만 writer에 위임한다.
- planning role은 internal-only다.
- `skills/`가 canonical source다.
- `.agents/skills`는 install-time legacy overlay일 뿐 canonical source가 아니다.
- generated file은 직접 수정하지 않고 source를 고친 뒤 sync로 재생성한다.

## Detailed Policy Files

- [00-core.md](docs/policy/00-core.md)
- [10-routing.md](docs/policy/10-routing.md)
- [20-workflows.md](docs/policy/20-workflows.md)
