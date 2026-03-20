---
name: multi-work
description: >
  Explicit multi-agent work entry that explores first and routes to planning,
  task-bundle execution, or direct execution.
---

# Multi Work

This is the default entry point for general work requests.
Always start with multi-agent exploration, then route to planning, task-bundle execution, or direct execution based on the evidence.

## Trigger

- `/multi-work`
- `$multi-work`
- `multi-work`

## Hard Rules

- Always begin with multi-agent exploration. Use at least 2 helpers.
- If multi-agent fan-out is unavailable in the runtime, report blocked instead of collapsing to single-agent work.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- In plan mode, do read-only exploration and produce only the plan.
- Even in the direct execution lane, never skip exploration and jump straight into implementation.
- Keep slice and writer decisions aligned with `policy/workflow.toml`, `scripts/workflow_contract.py`, and the existing `design-task` / `implement-task` contracts.
- Do not auto-run review. Keep multi-agent review as a separate explicit `multi-review` step.

## Workflow

1. Read `${SKILL_DIR}/references/routing-contract.md` and choose the helper combination that matches the request type.
2. Always execute multi-agent exploration first.
3. After helper fan-out, do only `wait` and result collection until results return. Pause additional file reads and searches in the main agent.
4. Decide between plan mode, approved task-bundle execution, and direct execution only after helper results return, using the routing contract and workflow helper rules.
5. When routing to `design-task` or `implement-task`, follow those skill contracts as-is.
6. Even in direct execution, keep the existing `split-replan`, `small slices + run-to-boundary`, and writer guardrails intact.
7. If review is needed after direct execution, leave an explicit `multi-review` next step instead of auto-running it.

## Required References

- helper matrix, routing matrix, direct execution guardrail: `${SKILL_DIR}/references/routing-contract.md`
- long-running planning and task-bundle design contract: `skills/design-task/SKILL.md`
- approved task-bundle execution contract: `skills/implement-task/SKILL.md`

## Validation

- Confirm the helper set contains at least 2 agents.
- Confirm the main agent does not continue file reads or searches between helper fan-out and result collection.
- Confirm plan mode produces read-only planning only.
- Confirm direct execution still preserves `split-replan` and writer thresholds.
- Confirm direct execution closeout does not auto-run review.
