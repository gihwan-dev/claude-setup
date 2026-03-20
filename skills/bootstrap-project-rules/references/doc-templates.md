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

## `README.md` Managed Section Markers

root `README.md` 갱신은 아래 marker 안에서만 수행한다.

```markdown
<!-- bootstrap-project-rules:start -->
...managed content...
<!-- bootstrap-project-rules:end -->
```

## `README.md` Managed Section

- `AI Workflow`
- implementation rules doc link
- task contract update rule
