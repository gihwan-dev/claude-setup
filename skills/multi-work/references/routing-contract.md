# Multi Work Routing Contract

This reference is for the main orchestrating thread only. Helpers do not read
this file.

## Routing Inputs

Lock these before emitting a ready routing result:

- `routing_mode` — `homogeneous` or `heterogeneous`
- `worker_agent_name` — required when `routing_mode=homogeneous`
- `shard_basis` — the dimension used to split helper work
- `handoff_target` — usually `$design-task` or `$parallel-workflow`

If any locked input is missing and cannot be derived from evidence, fail closed.

## Routing Mode Rules

- Default to `homogeneous`.
- `homogeneous` means every parallel helper uses the same agent type. Example:
  `web-researcher x4`.
- `heterogeneous` is allowed only when distinct helper lenses are explicitly
  required and the split is still easy to explain.
- If a request expects same-type fan-out but the selected helper set becomes
  mixed, stop and report `blocked`.

## Helper Matrix

| Situation | Required helpers |
|-----------|------------------|
| Basic repo discovery | built-in `explorer` x2 |
| Structural boundary judgment | `explorer` + `structure-reviewer` |
| External docs or official references | `web-researcher` x2 or baseline pair + `web-researcher` |
| Browser reproduction or visual evidence | `browser-explorer` x2 or matching pair + `browser-explorer` |
| Type or contract risk | baseline pair + `type-specialist` |
| React state model risk | baseline pair + `react-state-reviewer` |
| Test strategy risk | baseline pair + `test-engineer` |

The minimum helper count is always 2.

## Helper Return Contract

Each helper returns this compact shape:

- `summary` — short paragraph or bullets
- `evidence` — file paths, symbols, or citations
- `target_paths` — likely scope paths
- `recommended_next_step` — the exact next action
- `confidence` — `high`, `medium`, or `low`

If a helper cannot return that shape, it reports `blocked`.

## Fail-Closed Rules

Stop and do not emit a ready routing result when any of these are true:

- `routing_mode=homogeneous` but `worker_agent_name` is not locked
- helper evidence implies mixed helper types for a same-type fan-out request
- shard basis is unclear or overlaps heavily
- shared-file ownership is central to the work
- implementation, review, or task-bundle design is being requested from
  `multi-work`

Allowed outcomes in those cases:

- `blocked`
- `split-replan`
- handoff to `$design-task`

## Escalation Response Matrix

| Helper signal | Main-thread action |
|---|---|
| `confidence=high` | Synthesize and emit routing result |
| `confidence=medium` | Emit routing result only if shard basis is still clear |
| `confidence=low` | `split-replan` or re-dispatch with tighter scope |
| `blocked` | Immediate fail-closed result |
| conflicting evidence | surface the conflict and mark handoff not ready |

## Handoff Readiness

Use only these values:

- `ready` — routing is locked and the next skill can start
- `blocked` — missing routing inputs or conflicting evidence
- `split-replan` — work must be re-sliced before any further handoff

`multi-work` never claims that execution or review is complete. It only states
whether routing is ready.
