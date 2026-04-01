---
name: parallel-workflow
description: >
  Standard execution workflow for all approved task-bundle slices. Invoke only
  when the user explicitly writes "parallel-workflow" or "$parallel-workflow".
  Uses a 3-CSV runtime under `runs/parallel-workflow/<slice-id>/` for
  information collection, implementation, and review. CSV-1 (read) and CSV-3
  (review) are always parallel. CSV-2 (write) parallelism depends on
  execution_topology. Do not use for task-bundle planning or helper routing.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Parallel Workflow

Run an approved slice through the fixed 3-CSV runtime pipeline. This skill
owns runtime execution artifacts for all bundle slices. Planning stays with
`design-task`, and helper routing stays with `multi-work`.

## Trigger

- Invoke only when the user explicitly writes the exact skill name
  `parallel-workflow` or `$parallel-workflow`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- current slice from the bundle
- if the bundle blocks on a design decision, also read `SPEC_VALIDATION.md`
- if `task.yaml.source_of_truth.implementation` exists, read
  `IMPLEMENTATION_CONTRACT.md`
- if `delivery_strategy=ui-first`, also read `UX_SPEC.md`,
  `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/manifest.json`

## Hard Rules

- CSV-1 (info-collection) and CSV-3 (review) are always parallel with minimum 2
  helpers.
- CSV-2 (implementation) parallelism depends on `execution_topology`:
  `csv-fanout` uses multi-lane, `keep-local` uses single-lane,
  `hybrid` uses a mix.
- When `execution_topology=csv-fanout` and `assigned_agent_type` or
  `shard_basis` is not locked, hand off to `$multi-work`.
- When `execution_topology=keep-local`, use a fixed agent default (`explorer`
  for CSV-1, `verification-worker` plus a domain reviewer for CSV-3) and
  run CSV-2 as single-lane. Routing decisions are not needed, so
  `$multi-work` is not invoked.
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
2. Read `${SKILL_DIR}/references/csv-workflow-contract.md`.
3. Determine `execution_topology` from `task.yaml` (default: `keep-local`).
4. If `execution_topology=csv-fanout` and `assigned_agent_type` or
   `shard_basis` are not locked, stop with a `$multi-work` handoff.
5. Create `runs/parallel-workflow/<slice-id>/Documentation.md`.
6. Create `info-collection.csv`, `implementation.csv`, and `review.csv` using
   the required schemas from the reference file.
7. Run CSV-1 (`info-collection.csv`) with minimum 2 parallel helpers. For
   `keep-local`, default to `explorer x2`. Close routing, blockers, and row
   boundaries here.
8. Keep `implementation.csv` as a skeleton until CSV-1 completes. Then populate
   implementation rows. For `keep-local`, use a single implementation row.
   For `csv-fanout`, execute rows with the locked routing contract.
9. Run CSV-3 (`review.csv`) with minimum 2 parallel reviewers after
   implementation rows complete. Keep non-critical findings review-only
   unless the auto-fix gate is met.
10. Record cross-row blockers, shared-file decisions, and the final outcome
    in `Documentation.md`.
11. Update `STATUS.md` sections owned by this skill: `# Decisions made during
    implementation`, `# Verification results`, and `# Known issues / residual
    risk`. Leave `# Current slice`, `# Done`, and `# Next slice` to
    `implement-task`.

## Execution Modes

### csv-fanout

- CSV-1: multi-row, parallel info-collection by `assigned_agent_type`
- CSV-2: multi-row, conditionally parallel (`shared_file_touch`, `change_group_id`)
- CSV-3: multi-row, parallel review

### keep-local

- CSV-1: minimum 2 rows, parallel exploration (default `explorer x2`)
- CSV-2: single row, single-lane execution
- CSV-3: minimum 2 rows, parallel review (default `verification-worker` + domain reviewer)

### hybrid

- CSV-1: multi-row, parallel
- CSV-2: partial parallel + partial single-lane
- CSV-3: multi-row, parallel review

## Runtime Artifact Ownership

- `Documentation.md` is durable runtime memory for the main thread. Keep only
  current spec, routing decisions, blockers, cross-row decisions, and final
  conclusions there.
- CSV files are machine-readable ledgers. Do not replace `Documentation.md`
  with prose copied into CSV columns.
- Do not write runtime CSVs into the top-level task bundle.

## References

- `${SKILL_DIR}/references/csv-workflow-contract.md`
