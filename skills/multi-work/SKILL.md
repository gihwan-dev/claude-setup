---
name: multi-work
description: >
  Explicit multi-agent orchestration utility that explores first, selects
  helpers, and decomposes independent work units when boundaries are clear.
---

# Multi Work

This is an explicit multi-agent orchestration utility.
Always start with multi-agent exploration, then decide whether the work can be safely decomposed into independent work units.

## Trigger

- `/multi-work`
- `$multi-work`
- `multi-work`

## Hard Rules

- Always begin with multi-agent exploration. Use at least 2 helpers.
- If multi-agent fan-out is unavailable in the runtime, report blocked instead of collapsing to single-agent work.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Use decomposition only when the work can be framed as 2 or more independent work units with clear acceptance and merge boundaries.
- Shared-file edits, final integration, and final validation stay with the main thread or a designated integrator.
- Keep helper selection, decomposition thresholds, and execution guardrails aligned with `policy/workflow.toml`, `scripts/workflow_contract.py`, and this skill's orchestration contract.
- Do not auto-run review. Keep multi-agent review as a separate explicit `multi-review` step.

## Workflow

1. Read `${SKILL_DIR}/references/routing-contract.md` and choose the helper combination that matches the request type.
2. Always execute multi-agent exploration first.
3. After helper fan-out, do only `wait` and result collection until results return. Pause additional file reads and searches in the main agent.
4. After helper results return, decide whether the work should stay local, stop for `split-replan`, or decompose into independent work units.
5. Decompose only when each work unit has a clear owner, a clear output boundary, and limited dependency on sibling units.
6. Keep shared-file integration and final validation with the main thread or integrator instead of pushing them into parallel workers.
7. If review is needed after execution, leave an explicit `multi-review` next step instead of auto-running it.

## Required References

- helper matrix, orchestration matrix, and decomposition guardrails: `${SKILL_DIR}/references/routing-contract.md`

## Validation

- Confirm the helper set contains at least 2 agents.
- Confirm the main agent does not continue file reads or searches between helper fan-out and result collection.
- Confirm decomposition is used only for independent work units with clear merge boundaries.
- Confirm shared-file integration and final validation remain main-thread or integrator owned.
- Confirm execution closeout does not auto-run review.
