---
name: implement-task
description: >
  Execute the next approved non-parallel slice from task.yaml bundles. Invoke
  only when the user explicitly writes "implement-task" or "$implement-task".
  Follows the slice orchestration → bounded execution → verification → commit
  flow. If the current slice declares `Execution skill: parallel-workflow`,
  hand off instead of executing it directly.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Implement Task

Implement the next execution slice from an approved task bundle.

## Trigger

- Invoke only when the user explicitly writes the exact skill name `implement-task` or `$implement-task`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- if `task.yaml.agent_orchestration` exists, read it before choosing the execution lane. New bundles should include it.
- if `delivery_strategy=ui-first`, also read `task.yaml.source_of_truth.ux = UX_SPEC.md`, `task.yaml.source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `task.yaml.source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`
- if `task.yaml.source_of_truth.implementation` exists, read `IMPLEMENTATION_CONTRACT.md`
- if `execution_topology` is `csv-fanout` or `hybrid`, read only the static `task.yaml.orchestration` block
- if the bundle needs a blocking decision, read `SPEC_VALIDATION.md`

## Task Selection

- Multiple active task folders are a normal state.
- If no path is specified, build the active candidate set first.
- Auto-select only when there is exactly 1 candidate.
- If there are 2 or more candidates, always confirm with the user instead of auto-running.

## Core Flow

1. Read `STATUS.md` first. If `STATUS.md` is missing, create it with the fixed template sections. `task.yaml` is required.
2. If a path or slug is specified, use that task. Otherwise apply the candidate rule above as-is.
3. For bundle work, keep `task.yaml.success_criteria`, `major_boundaries`, and `delivery_strategy` as the implementation contract, and check `SPEC_VALIDATION.md` for blocking issues. If `task.yaml.source_of_truth.implementation` exists, also read `IMPLEMENTATION_CONTRACT.md` as a primary input.
4. If `task.yaml.agent_orchestration` exists and `strategy=manager`, lock the manager lane before code work starts. In that lane, the main thread may read bundle docs plus structured helper or worker output only.
5. Read the current slice contract in `EXECUTION_PLAN.md`. If the slice declares `Execution skill: parallel-workflow`, stop direct execution and hand off to `$parallel-workflow`.
6. If `delivery_strategy=ui-first`, read `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/manifest.json` together. `SLICE-1` reads checklist/layout/token/screen-flow plus interaction/a11y/microcopy sections. `SLICE-2` reads keyboard/focus, live semantics, state matrix/fixture, degradation, and task-based approval criteria.
7. Lock the current slice boundary, run structure preflight, then choose the bounded execution lane described by `agent_orchestration` and the slice-level orchestration fields. If the `split-first trigger` is on, do not append to the existing target file. Fix the decomposition boundary inside the same slice first, and fall back to an `exact split proposal` if the scope cannot be reduced.
   - Built-in `worker` delegation: if the slice touches 2+ files with clear boundaries and no shared-file edits, consider delegating. Parallel workers require no dependency between target files.
   - A `worker` handoff must include `target_path`, `change_spec`, `context_files`, `validation_command`, and `slice_budget`.
   - In manager mode, do not fall back to direct main-thread implementation when a worker lane blocks. Stop with `blocked + split/replan`, or re-route only through another bounded lane the bundle explicitly allows.
   - If a `worker` returns `status: final`, keep shared-file integration inside the designated integration owner lane.
   - For parallel workers, use `isolation: worktree` with independent git worktrees, then have the designated integration owner merge the resulting diffs.
   - `multi-work` is optional. Consider it only when the approved slice has 2+ independent work units with clear acceptance and merge boundaries.
8. Use `browser-explorer` only when browser reproduction or visual evidence is needed. The handoff must include `target URL or Electron entry`, `scenario checklist`, and `evidence checklist`.
9. In manager mode, send validation execution to the designated lane and use `verification-worker` to summarize the results. Direct main-thread validation fallback is forbidden. Legacy bundles without `agent_orchestration` may use the old main-thread focused-validation path.
10. If validation passes, commit the change and update `STATUS.md` with a manager-facing summary.
11. Default single-slice mode stops after 1 slice. Run-to-boundary mode repeats the same loop until a stop or replan condition is hit.

## Guardrails

- Do not implement outside bundle documents.
- If `validation_gate: blocking` still has blocking issues, do not begin implementation.
- If `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, or project implementation rules are unresolved, do not begin implementation.
- If `agent_orchestration.strategy=manager`, the main thread is orchestration-only. It may not collapse back to direct implementation, direct validation, or ad hoc shared-file merge.
- If `delivery_strategy=ui-first`, do not skip or merge the `SLICE-1 -> SLICE-2 -> SLICE-3+` order, and do not mix real API or integration diff into early UI slices.
- Preserve the `slice orchestration -> bounded execution lane -> verification summary -> commit` order.
- The default for hybrid mode is `small slices + run-to-boundary`.
- If the slice budget exceeds the small-slice guardrail (`repo-tracked files 3 or fewer`, net diff around `150 LOC`), fall back to `split/replan before execution`.
- If focused validation fails, do not commit and record the slice failure.
- If docs or other SSOT files change, finish the required sync and `--check` runs before exit.
- Built-in `worker` subagents do not edit files outside `target_path`. Shared files are integrated by the designated integration owner lane in manager mode.
- Built-in `worker` subagents do not perform git commit. Commit stays main-thread only.
- Do not let parallel built-in `worker` subagents edit the same file concurrently. If file-boundary conflicts are detected, switch back to sequential execution.
- Do not treat `multi-work` as a required lifecycle step. It is an optional routing pattern only, and `parallel-workflow`, built-in `worker` delegation, or `split/replan` remain the default fit checks.

## References

- Detailed execution rules, validation fallback, and STATUS contract: `references/execution-rules.md`
- For large approved slices with independent work units, consider a `$multi-work` handoff for routing.

## Validation

- Prefer validation commands from `EXECUTION_PLAN.md`.
- Use repo-aware fallback only when the documented validation command is empty.
- If you changed SSOT such as `skills` or `agent-registry`, run the matching sync plus `--check`.
- If you changed `skills`, include `python3 scripts/sync_skills_index.py --check`.
- If you changed `agent-registry`, include `python3 scripts/sync_agents.py --check`.
