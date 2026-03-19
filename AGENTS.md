<!-- AUTO-GENERATED from docs/policy. Do not edit directly. -->
<!-- Run: python3 scripts/sync_instructions.py -->

# Repository Guidance

루트 guidance는 얇게 유지한다. 세부 정책은 `docs/policy/*.md`, 작업 절차와 검증 명령은 `CONTRIBUTING.md`를 본다.

## Core Goal

- 메인 스레드는 전략과 의사결정에 집중한다.
- generated 파일은 직접 수정하지 않고 source를 고친 뒤 sync로 재생성한다.

## Source Of Truth

- 정책: `docs/policy/*.md`
- agent: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- skill: `skills/`
- `.agents/skills`는 install-time legacy overlay다.

## Important Constraints

- delegated lane에서 writer 위임은 조건부다.
- planning role은 internal-only다.

## Detailed Policy Files

- [00-core.md](docs/policy/00-core.md)
- [10-routing.md](docs/policy/10-routing.md)
- [20-workflows.md](docs/policy/20-workflows.md)
