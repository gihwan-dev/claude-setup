---
name: multi-work
description: >
  Routing-only multi-agent orchestration utility. Use when the user writes
  "/multi-work" or "$multi-work", or when a task needs an explicit helper
  routing decision before planning or execution. Produces a Routing Strategy
  only. Do not use for implementation, review loops, or task-bundle authoring.
allowed-tools: Read, Grep, Glob, Agent
---

# Multi Work

`multi-work` decides how helpers should be routed in parallel. It does not
implement code, run review loops, or design task bundles. Its only artifact is
a `Routing Strategy` handoff that another skill or the user can execute.

## Scope Boundary

In scope:

- choosing helper types
- choosing routing mode and shard basis
- deciding whether homogeneous fan-out is safe
- determining whether routing is ready or must fail closed

Out of scope:

- code edits or execution
- review ownership or review loops
- task-bundle document creation
- runtime CSV generation or maintenance
- shared-file integration strategy beyond marking it as out of scope

## Dispatch Prompt Contract

Each helper prompt contains exactly these items and nothing else:

1. `Exploration target` — files, directories, or the concrete question.
2. `Scope boundary` — in scope and out of scope for that helper.
3. `Return shape` — the Helper Return Contract from `routing-contract.md`.

Helper prompts contain only exploration target, scope boundary, and return shape.

## Workflow

0. If the request is too ambiguous to choose a shard basis, ask 1 concise
   scoping question before dispatching helpers.
1. Read `${SKILL_DIR}/references/routing-contract.md`.
2. Choose the routing mode. Default to `homogeneous`.
3. Lock `worker_agent_name` before dispatch when routing mode is
   `homogeneous`. If it is not locked, fail closed and hand off to
   `split-replan` or `$plan`.
4. Compose helper prompts using the Dispatch Prompt Contract.
5. Dispatch at least 2 helpers. If multi-agent fan-out is unavailable, report
   `blocked` instead of falling back to solo exploration.
6. While helpers run, do not reread the repo or add new ad hoc searches.
7. Synthesize helper output into a `Routing Strategy`.
8. If helpers return low confidence, blocked status, or conflicting evidence,
   follow the fail-closed rules in `routing-contract.md`.
9. Stop after the `Routing Strategy` is written. If runtime execution is the
   next step, hand off to `$build`. If planning is the next step,
   hand off to `$plan`.

## Routing Strategy Output

In planning or collaborator modes, the output must include a `Routing Strategy`
section with these fields only:

- `Helper plan` — which helpers were used and why
- `Routing mode` — `homogeneous` or `heterogeneous`
- `Agent allocation` — helper type plus count or shard ownership
- `Shard basis` — what each helper was split by
- `Fail-closed rule` — what blocks execution when routing is underspecified
- `Handoff readiness` — whether the next step is ready, blocked, or split-replan

### Example

```md
## Routing Strategy

- Helper plan: `explorer x2` for repo discovery, `structure-reviewer x1` for
  boundary risk
- Routing mode: `homogeneous`
- Agent allocation: `explorer x2`, shard-A=`src/search/**`, shard-B=`src/data/**`
- Shard basis: module boundary
- Fail-closed rule: if shared-file ownership is unclear, do not route execution;
  hand off to `split-replan`
- Handoff readiness: ready for `$plan`
```

## Required References

- `${SKILL_DIR}/references/routing-contract.md`

## Alignment

Keep helper selection, routing defaults, and fail-closed behavior aligned with
`${SKILL_DIR}/references/routing-contract.md`. Installed runs must not depend on
repo-root helpers or repo-local scripts.
