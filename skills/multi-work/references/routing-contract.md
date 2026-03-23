# Multi Work Orchestration Contract

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| Basic repo or code exploration | built-in `explorer`, `structure-reviewer` |
| External technical judgment or official docs needed | Baseline pair + `web-researcher` |
| Browser reproduction or visual evidence needed | Matching pair + `browser-explorer` |

The minimum helper count is always 2.

## Helper Return Contract

Each helper should return a compact structured payload the main thread can synthesize without broad rereads.

- `summary` — 1 short paragraph or bullet list of what matters.
- `evidence` — concrete file paths, symbols, or external citations that support the summary.
- `target_paths` — files or directories the helper believes are in scope.
- `recommended_next_step` — the exact next action the orchestrator should take.
- `confidence` — `high`, `medium`, or `low`.

If a helper cannot produce this shape, it should report `blocked` instead of substituting a long free-form narrative.

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

For planning or collaborator modes, the main output must also include an `Orchestration Strategy` section with the following fields:

- `Helper plan`
- `Execution owner`
- `Allowed main-thread actions`
- `Fallback`
- `Review boundary`

## Decomposition Guardrail

- Do not skip multi-agent exploration.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- After helper fan-out, the main agent should synthesize structured helper output first and treat broad rereads as a failure mode.
- Reuse helper and slice-budget decisions from `scripts/workflow_contract.py`.
- Broad or poorly bounded work means `split-replan`.
- Use decomposition only when each unit has independent acceptance criteria, a fixed target or output boundary, and sparse dependency on sibling units.
- Shared-file integration and final validation stay with the designated integration or verification lane.
- If those conditions are not met, keep the work local instead of forcing parallel execution.

## Review Boundary

- `multi-work` does not auto-run review.
- Keep multi-agent review as an explicit `multi-review` step.
