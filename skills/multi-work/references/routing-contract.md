# Multi Work Orchestration Contract

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| Basic repo or code exploration | built-in `explorer`, `structure-reviewer` |
| External technical judgment or official docs needed | Baseline pair + `web-researcher` |
| Browser reproduction or visual evidence needed | Matching pair + `browser-explorer` |
| Type or interface contract changes are central | Baseline pair + `type-specialist` |
| React state model judgment is needed | Baseline pair + `react-state-reviewer` |
| Test strategy judgment is needed | Baseline pair + `test-engineer` |

The minimum helper count is always 2.

## Helper Return Contract

Each helper should return a compact structured payload the main thread can synthesize without broad rereads.

- `summary` — 1 short paragraph or bullet list of what matters.
- `evidence` — concrete file paths, symbols, or external citations that support the summary.
- `target_paths` — files or directories the helper believes are in scope.
- `recommended_next_step` — the exact next action the orchestrator should take.
- `confidence` — `high`, `medium`, or `low`.

If a helper cannot produce this shape, it should report `blocked` instead of substituting a long free-form narrative.

## Escalation Response Matrix

| Helper Signal | Main Thread Action |
|---|---|
| confidence: high | Synthesize and proceed to next step |
| confidence: medium | Synthesize, but evaluate whether an additional targeted fan-out is needed |
| confidence: low | `split-replan`, or re-dispatch with additional context files |
| blocked | Immediate `split-replan`; record the reason in the Orchestration Strategy |
| conflicting evidence across helpers | Surface the conflict explicitly and request user judgment |

## Timeout Policy

- If a helper does not return within a reasonable time, treat it as stale and synthesize from the remaining results.
- A single stale or failed helper must not block the entire fan-out.
- Record the absent helper and its expected contribution in the Orchestration Strategy so downstream steps can compensate.

## Conflict Resolution

- When helpers return conflicting evidence, prefer the one with higher confidence.
- At equal confidence, surface the conflict in the Orchestration Strategy and request user judgment.
- When structural judgment (`structure-reviewer`) conflicts with domain judgment (`type-specialist`, `react-state-reviewer`), default to structural judgment but record the rationale.

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
