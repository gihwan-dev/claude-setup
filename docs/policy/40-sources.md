## Source of Truth

- 정책 authoring source: `docs/policy/*.md`
- machine-readable workflow/structure contract: `policy/workflow.toml`
- compiled source doc: `INSTRUCTIONS.md`
- Codex projection: `AGENTS.md`
- Claude projection: `CLAUDE.md`
- agent contract: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- generated projections: `agents/*.md`, `dist/codex/agents/*.toml`, `dist/codex/config.managed-agents.toml`
- skill canonical source: `skills/`
- skill index + manifest: `skills/INDEX.md`, `skills/manifest.json`
- `skills/_shared` 같은 internal asset은 catalog/index/generated skill set에는 포함하지 않고, consuming skill의 상대경로 참조를 위해 install-time에만 별도 배포한다.
- legacy skill overlay: `.agents/skills` (설치 호환용, 기본 source 아님)
- long-running task source of truth: `tasks/<task-path>/task.yaml` bundle. 문서 구조는 `workflow.toml [task_documents]`에서 관리한다.
- `STATUS.md`는 오케스트레이터 메타 상태 문서로 유지한다.
- legacy task만 `PLAN.md`를 유지하고, 새 task에는 `task.yaml` bundle을 사용한다.

## 세부 규칙

- helper agent 목록과 orchestration 계약은 `workflow.toml [projection]`과 각 `agent.toml [orchestration]`에서 관리한다.
- projected specialized agent(`browser-explorer`)는 generated projection으로 설치될 수 있지만 `required_helper_agent_ids`에는 포함하지 않는다.
- generated projection과 compiled doc은 직접 수정하지 않고 sync로 재생성한다.
