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
- long-running task public surface: `design-task`, `implement-task`
- 새 long-running task source of truth는 `tasks/<task-path>/task.yaml`과 bundle 문서(`README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, 전문 문서들)다.
- greenfield/new-project post-design bootstrap이 적용되면 repo-level implementation rules source는 `docs/ai/ENGINEERING_RULES.md`다.
- `task.yaml.delivery_strategy`는 새 bundle의 machine-readable execution contract다.
- `task.yaml.source_of_truth.implementation`은 optional task supplement pointer로 `IMPLEMENTATION_CONTRACT.md`를 가리킬 수 있다.
- `STATUS.md`는 새 task와 legacy task 모두에서 오케스트레이터 메타 상태 문서로 유지한다.
- legacy compatibility task만 `PLAN.md`를 source of truth로 유지하고, 새 task에는 `PLAN.md`를 만들지 않는다.
- `design-task`는 continuity gate를 통과한 경우에만 기존 task를 재사용한다. 새 task는 `task.yaml`, legacy task는 `PLAN.md`를 기준으로 비교하고 `delivery_strategy`가 다르면 새 task를 만든다.

## 세부 규칙

- planning role은 `design-task` 내부 fan-out 전용이며 user-facing install/projection 대상이 아니다.
- `monitor`는 built-in long-polling/wait 역할로만 문서화하고 repo-managed projection은 만들지 않는다.
- helper agent(`worker`, `explorer`, `verification-worker`, `architecture-reviewer`, `code-quality-reviewer`, `type-specialist`, `test-engineer`, `module-structure-gatekeeper`, `frontend-structure-gatekeeper`)는 runtime helper로 보장되어야 하며 각 `agent.toml`의 `[orchestration]` (`blocking_class`, `result_contract`, `close_protocol`, `late_result_policy`, `timeout_policy`, `allowed_close_reasons`)을 SSOT로 유지한다.
- projected specialized agent(`browser-explorer`)는 generated projection으로 설치될 수 있지만 `required_helper_agent_ids`에는 포함하지 않는다. 명시적인 브라우저 상호작용 task에서만 선택적으로 호출한다.
- `policy/workflow.toml`의 `[structure_policy]`는 file role별 limit, split-first behavior, legacy oversized file rule의 machine-readable SSOT다.
- generated projection과 compiled doc은 직접 수정하지 않고 sync로 재생성한다.
