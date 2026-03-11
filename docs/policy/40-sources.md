## Source of Truth

- 정책 authoring source: `docs/policy/*.md`
- compiled source doc: `INSTRUCTIONS.md`
- Codex projection: `AGENTS.md`
- Claude projection: `CLAUDE.md`
- agent contract: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- generated projections: `agents/*.md`, `dist/codex/agents/*.toml`, `dist/codex/config.managed-agents.toml`
- skill canonical source: `skills/`
- skill index + manifest: `skills/INDEX.md`, `skills/manifest.json`
- `skills/_shared` 같은 internal asset은 catalog/index/generated skill set에는 포함하지 않고, consuming skill의 상대경로 참조를 위해 install-time에만 별도 배포한다.
- legacy skill overlay: `.agents/skills` (설치 호환용, 기본 source 아님)
- long-running task public surface: `design-task`, `implement-task`

## 세부 규칙

- planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- `monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection은 만들지 않는다.
- helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)는 runtime helper로 보장되어야 하며 각 `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)을 SSOT로 유지한다.
- generated projection과 compiled doc은 직접 수정하지 않고 sync로 재생성한다.
