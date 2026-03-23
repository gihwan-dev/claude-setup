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

## Structure And Handoff Rules

- Before each slice, lock structure preflight first: target file role, expected post-change LOC, and whether a split is needed.
- The default for hybrid mode is `small slices + run-to-boundary`.
- Allow only 1 pre-edit status report for structure preflight. Do not ask for extra checkpoints before the first edit.
- If the split-first trigger is on, do not append to the target file. Either extract a new module within the same slice or fall back to `blocked + exact split proposal`.
- If the handoff is a broad `setup` / `skeleton` / `wrapper` / `docs` handoff, or a PREP-0 style handoff that exceeds the hard slice guardrail, revert to `split/replan before execution`.
- Before exit, the main thread rechecks materially affected docs such as README, `docs/**`, task-bundle docs, `openapi.yaml`, `schema.json`, architecture or change docs, and workflow or SSOT runbook docs.
- Apply required doc diffs or generated projection sync during implementation before focused validation.

## Validation Fallback

- Prefer validation commands from `EXECUTION_PLAN.md`.
- Use repo-aware fallback only when the documented validation command is empty.
- Focused validation is owned by the main thread.
- The default focused validation is `one target-specific validation + one low-cost check`.
- Use full-repo validation only when shared or public boundaries changed.
- In JS or TS repos, choose the package manager from `package.json` and lockfiles, and run only scripts that actually exist.
- In Python repos, treat `pyproject.toml` or `tests/` / `test_*.py` as signals that `python3 -m unittest discover` is a candidate fallback.
- If a safe default validation cannot be inferred, stop before execution and get confirmation.
- If SSOT sync or checks are required, use the fallback below.
  - `skills`: `python3 scripts/sync_skills_index.py` + `python3 scripts/sync_skills_index.py --check`
  - `agent-registry`: `python3 scripts/sync_agents.py` + `python3 scripts/sync_agents.py --check`

## CSV Fan-out Execution Rules

### Environment Detection

- Codex environment: determine this from `spawn_agents_on_csv` availability.
- Claude Code environment: fall back to sequential `keep-local` execution.

### Row Worker Constraints

- Each row worker may create or edit files only at the CSV `target_path`.
- Follow layout and import rules from `GLOBAL_CONTEXT.md`.
- Row workers do not reference output from other rows. (No cross-row reference.)
- Shared files such as barrel exports, route registration, and `package.json` are off-limits.

### Integrator Role

- After all row workers finish, the integrator merges shared files.
- Update barrel exports, route registration, and similar files using the integrator-only file list from `MERGE_POLICY.md`.
- If row outputs touch the same shared-file section, apply them in `row_id` order.

### Failure Recovery

- Retry a failed row once automatically.
- If it still fails, record that row as `failed` and continue the rest.
- If 50 percent or more of all rows fail, stop slice execution.

### Row-level Continuity

- Previously successful `row_id` -> skip.
- `row_id` whose acceptance criteria or `target_path` changed -> re-execute.
- Newly added `row_id` -> append.
- Deleted `row_id` -> superseded (preserve the result).

### STATUS.md Extension (`csv-fanout`)

Record the following extra fields in `STATUS.md` for a `csv-fanout` slice.

- total row count
- counts for success / failure / skip / superseded
- retry count
- integrator result (shared-file merge success or failure)

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

### Update Rules

- `# Current slice`: record the slice targeted by this run.
- `# Done`: summarize completed outcomes and user or system impact instead of listing implementation trivia.
- `# Decisions made during implementation`: record decisions that affect the next slice or public boundaries, plus doc-impact judgments.
- `# Verification results`: record validation commands, pass or fail results, doc or SSOT sync-check results, commit attempt results, and only the key failure causes.
- `# Known issues / residual risk`: record remaining risks and unresolved issues.
- `# Next slice`: record the next execution target, prerequisites, and boundaries to inspect first.
- On the first run that creates `STATUS.md`, record the fact that the template was created in `# Done` or `# Decisions made during implementation`.
- Keep the design-stage initial bundle default of `# Current slice=Not started.` and `# Next slice=SLICE-1`.
