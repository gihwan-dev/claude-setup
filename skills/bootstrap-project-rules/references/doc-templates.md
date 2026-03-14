# Document Templates

`bootstrap-project-rules`가 생성하거나 갱신하는 문서는 아래 section order를 따른다.

## `docs/ai/ENGINEERING_RULES.md`

```markdown
# Project Profile
# Locked Decisions
# Architecture Boundaries
# Coding Conventions
# Validation Commands
# Dependency Policy
# Decision Update Rules
# Prohibited Patterns
```

## `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md`

```markdown
# Inputs Read
# Task-Specific Decisions
# Allowed Core Libraries
# Deferred Decisions and Trigger
# Validation Overrides
# Open Risks
```

## Managed Section Markers

모든 root 문서 갱신은 아래 marker 안에서만 수행한다.

```markdown
<!-- bootstrap-project-rules:start -->
...managed content...
<!-- bootstrap-project-rules:end -->
```

## `AGENTS.md` Managed Section

- Read first docs
- Exact commands
- Architecture map
- Hard rules / known quirks

## `CLAUDE.md` Managed Section

- Short memory bullets
- `@docs/ai/ENGINEERING_RULES.md`
- task-specific contract read reminder

## `README.md` Managed Section

- `AI Workflow`
- implementation rules doc link
- task contract update rule
