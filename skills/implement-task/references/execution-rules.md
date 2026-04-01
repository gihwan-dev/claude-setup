# Execution Rules

This reference collects the detailed execution rules for `implement-task`. `SKILL.md` keeps only the core flow; read the rules below only when needed.

## Task Selection Rules

1. If the user specifies a slug or path, use that task.
2. If no path is given, build the active candidate set. (Only tasks with an unfinished `Next slice` or currently executable status count.)
3. Auto-select only when there is exactly 1 candidate.
4. If there are 2 or more candidates, always confirm with the user instead of auto-running.
5. If there are 0 candidates, consult the most recently modified task but do not execute before user confirmation.

## Mode Rules

- If the user says `continue`, execute exactly 1 next slice for the current task.
- If the user explicitly says `until done` or `until a stop condition is hit`, use a continuous execution loop.
- During continuous execution, stop immediately and update only `STATUS.md` when any of the following happens.
  - focused validation fails
  - commit fails, including failed retry with `--no-verify`
  - implementation stops with `blocked + exact split proposal`
  - a bundle still has unresolved blocking issues in `SPEC_VALIDATION.md`
  - the stop or replan condition in `EXECUTION_PLAN.md` is hit
  - public-boundary drift appears
  - a decision gap appears before the next slice can start

## Pre-Execution Gate Rules

These rules are checked before starting the 3-CSV pipeline. If any gate
fails, stop before execution.

- If the slice budget exceeds the small-slice guardrail, fall back to
  `split/replan before execution`.
- If the handoff is a broad `setup` / `skeleton` / `wrapper` / `docs`
  handoff that exceeds the hard slice guardrail, revert to `split/replan`.
- If SSOT sync or checks are required after commit, use the fallback below.
  - `skills`: `python3 scripts/sync_skills_index.py` + `python3 scripts/sync_skills_index.py --check`
  - `agent-registry`: `python3 scripts/sync_agents.py` + `python3 scripts/sync_agents.py --check`

## 3-CSV Execution Rules

- All bundle slices execute through the 3-CSV pipeline. To start execution,
  read `${SKILL_DIR}/references/csv-execution-rules.md` and run its full
  pipeline for the current slice. Do not skip this read step.
- `implement-task` owns task selection, STATUS.md finalization, and commit.
  The 3-CSV pipeline owns runtime artifacts and execution-detail STATUS
  sections.

## STATUS Contract

### Template

```markdown
# Current slice
# Done
# Decisions made during implementation
# Verification results
# Known issues / residual risk
# Next slice
```

### Ownership

The 3-CSV pipeline writes execution details into `# Decisions made during
implementation`, `# Verification results`, and `# Known issues / residual risk`.
`implement-task` finalizes `# Current slice`, `# Done`, and `# Next slice`
after commit.

### Update Rules

- `# Current slice`: record the slice targeted by this run. (`implement-task`)
- `# Done`: summarize completed outcomes and user or system impact. (`implement-task`)
- `# Decisions made during implementation`: record decisions that affect the next slice or public boundaries. (3-CSV pipeline)
- `# Verification results`: record validation commands, pass or fail results, and key failure causes. (3-CSV pipeline)
- `# Known issues / residual risk`: record remaining risks and unresolved issues. (3-CSV pipeline)
- `# Next slice`: record the next execution target, prerequisites, and boundaries. (`implement-task`)
- On the first run that creates `STATUS.md`, record the fact that the template was created in `# Done`.
- Keep the design-stage initial bundle default of `# Current slice=Not started.` and `# Next slice=SLICE-1`.
