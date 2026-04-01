---
name: parallel-workflow
description: >
  Parallel execution workflow for approved task-bundle slices. Invoke only when
  the user explicitly writes "parallel-workflow" or "$parallel-workflow". Uses
  a 3-CSV runtime under `runs/parallel-workflow/<slice-id>/` for information
  collection, implementation, and review. Do not use for task-bundle planning
  or helper routing.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Parallel Workflow

Run an approved parallel slice through a fixed 3-CSV runtime pipeline. This
skill owns runtime execution artifacts. Planning stays with `design-task`, and
helper routing stays with `multi-work`.

## Trigger

- Invoke only when the user explicitly writes the exact skill name
  `parallel-workflow` or `$parallel-workflow`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- current slice with `Execution skill: parallel-workflow`
- if the bundle blocks on a design decision, also read `SPEC_VALIDATION.md`
- if `task.yaml.source_of_truth.implementation` exists, read
  `IMPLEMENTATION_CONTRACT.md`

## Hard Rules

- When `assigned_agent_type` or `shard_basis` is not locked, stop and hand off
  to `$multi-work`.
- Always create or update all 4 runtime artifacts under
  `runs/parallel-workflow/<slice-id>/`:
  - `Documentation.md`
  - `info-collection.csv`
  - `implementation.csv`
  - `review.csv`
- `implementation.csv` must exist even before implementation rows are finalized.
- Finalize implementation rows only after `info-collection.csv` closes.
- If `shared_file_touch=Y`, force either `parallelizable=false` or a single lane
  by `change_group_id`.
- Auto-fix is allowed only for `critical` or `blocker` findings that have a
  row-local validation command and a small diff boundary.

## Workflow

1. Resolve the bundle path and current slice.
2. Confirm the slice declares `Execution skill: parallel-workflow`. If not,
   stop and point the caller back to the slice contract.
3. Read `${SKILL_DIR}/references/csv-workflow-contract.md`.
4. If `assigned_agent_type` or `shard_basis` are not locked in the bundle or
   user request, stop with a `$multi-work` handoff.
5. Create `runs/parallel-workflow/<slice-id>/Documentation.md`.
6. Create `info-collection.csv`, `implementation.csv`, and `review.csv` using
   the required schemas from the reference file.
7. Run CSV-1 (`info-collection.csv`) first and close routing, blockers, and row
   boundaries there.
8. Keep `implementation.csv` as a skeleton until CSV-1 completes. Then populate
   implementation rows and execute them with the locked routing contract.
9. Run CSV-3 (`review.csv`) after implementation rows complete. Keep
   non-critical findings review-only unless the auto-fix gate is met.
10. Record cross-row blockers, shared-file decisions, fallback reasons, and the
    final outcome in `Documentation.md`.
11. Update `STATUS.md` with a concise execution summary and the next required
    action.

## Runtime Artifact Ownership

- `Documentation.md` is durable runtime memory for the main thread. Keep only
  current spec, routing decisions, blockers, cross-row decisions, and final
  conclusions there.
- CSV files are machine-readable ledgers. Do not replace `Documentation.md`
  with prose copied into CSV columns.
- Do not write runtime CSVs into the top-level task bundle.

## References

- `${SKILL_DIR}/references/csv-workflow-contract.md`
