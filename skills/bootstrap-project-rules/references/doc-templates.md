# Document Templates

Documents created or updated by `bootstrap-project-rules` must follow the section order below.

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

Update the root `README.md` only inside the markers below.

```markdown
<!-- bootstrap-project-rules:start -->
...managed content...
<!-- bootstrap-project-rules:end -->
```

## `README.md` Managed Section

- `AI Workflow`
- implementation-rules doc link
- task-contract update rule
