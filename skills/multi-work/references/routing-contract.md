# Multi Work Routing Contract

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| Basic repo or code exploration | `explorer`, `structure-reviewer` |
| External technical judgment or official docs needed | Baseline pair + `web-researcher` |
| Browser reproduction or visual evidence needed | Matching pair + `browser-explorer` |

The minimum helper count is always 2.

## Routing Matrix

| Condition | Route |
|-----------|-------|
| plan mode | `design-task` |
| User asks for planning or design | `design-task` |
| Execute the next slice of an approved task bundle | `implement-task` |
| New work is large or ambiguous | `design-task` |
| Continuity judgment or bundle creation is needed | `design-task` |
| Work is small and bounded | direct execution |

`multi-work` is the top-level wrapper.
Actual task-bundle design and execution rules remain delegated to `design-task` and `implement-task`.

## Direct Execution Guardrail

- Even in direct execution, do not skip multi-agent exploration.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Reuse slice-budget decisions from `scripts/workflow_contract.py`.
- Broad handoff means `split-replan`.
- Only allowed slices proceed under `small slices + run-to-boundary`.
- Use writer only when the existing writer conditions are satisfied.
- Use parallel writers only when file boundaries are independent and shared-file integration stays with the main thread.
- If multiple active task-bundle candidates exist, follow the candidate confirmation rules from `implement-task`.

## Review Boundary

- `multi-work` does not auto-run review.
- Keep multi-agent review as an explicit `multi-review` step.
