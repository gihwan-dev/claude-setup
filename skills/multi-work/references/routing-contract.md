# Multi Work Orchestration Contract

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| Basic repo or code exploration | `explorer`, `structure-reviewer` |
| External technical judgment or official docs needed | Baseline pair + `web-researcher` |
| Browser reproduction or visual evidence needed | Matching pair + `browser-explorer` |

The minimum helper count is always 2.

## Orchestration Matrix

| Condition | Orchestration mode |
|-----------|--------------------|
| Repo or code understanding is still weak | helper fan-out + main-thread synthesis |
| External technical judgment or official docs are required | add `web-researcher` |
| Browser reproduction or visual evidence is required | add `browser-explorer` |
| Work can be split into 2 or more independent work units | bounded multi-work decomposition |
| Shared-file edits or sequencing dependencies dominate | keep local or stop with `split-replan` |
| Acceptance boundaries are still unclear after exploration | stop with `split-replan` |

`multi-work` is an explicit orchestration utility, not a task-lifecycle router.

## Decomposition Guardrail

- Do not skip multi-agent exploration.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Reuse helper and slice-budget decisions from `scripts/workflow_contract.py`.
- Broad or poorly bounded work means `split-replan`.
- Use decomposition only when each unit has independent acceptance criteria, a fixed target or output boundary, and sparse dependency on sibling units.
- Shared-file integration and final validation stay with the main thread or integrator.
- If those conditions are not met, keep the work local instead of forcing parallel execution.

## Review Boundary

- `multi-work` does not auto-run review.
- Keep multi-agent review as an explicit `multi-review` step.
