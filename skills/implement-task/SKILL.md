---
name: implement-task
description: >
  Execute the next approved slice from `task.yaml` bundles. Invoke only when
  the user explicitly writes `implement-task` or `$implement-task`. Use the
  `slice implementation -> main focused validation -> commit -> STATUS.md
  update` flow for the next approved slice.
---

# Implement Task

Implement the next execution slice from an approved task bundle.

## Trigger

- Invoke only when the user explicitly writes the exact skill name `implement-task` or `$implement-task`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- if `delivery_strategy=ui-first`, also read `task.yaml.source_of_truth.ux = UX_SPEC.md`, `task.yaml.source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `task.yaml.source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`
- if `task.yaml.source_of_truth.implementation` exists, read `IMPLEMENTATION_CONTRACT.md`
- if `execution_topology=csv-fanout`, read `GLOBAL_CONTEXT.md`, `work-items/*.csv`, `MERGE_POLICY.md`, and the `task.yaml.orchestration` block
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
3a. Check `task.yaml.execution_topology`. If it is `csv-fanout` or `hybrid`, also read `GLOBAL_CONTEXT.md`, `MERGE_POLICY.md`, and the `orchestration` block.
3b. If it is `csv-fanout`, inspect the `work-items/*.csv` file for the current slice.
3c. In Codex environments with `spawn_agents_on_csv`, run row workers in parallel per CSV row. Without Codex, fall back to sequential `keep-local` fallback execution.
3d. After row workers finish, collect the output CSV. Retry failed rows once. Abort when 50 percent or more of rows fail.
3e. In `csv-fanout`, let the integrator merge shared files such as barrel exports or route registration according to `MERGE_POLICY.md`.
4. If `delivery_strategy=ui-first`, read `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/manifest.json` together. `SLICE-1` reads checklist/layout/token/screen-flow plus interaction/a11y/microcopy sections. `SLICE-2` reads keyboard/focus, live semantics, state matrix/fixture, degradation, and task-based approval criteria.
5. Lock the current slice boundary, run structure preflight, then apply the code or doc diff. If the `split-first trigger` is on, do not append to the existing target file. Fix the decomposition boundary inside the same slice first, and fall back to an `exact split proposal` if the scope cannot be reduced.
5a. Built-in `worker` delegation rule: if the current slice touches 2 or more files, the file boundaries are clear, and shared-file edits are unnecessary, consider delegating to the built-in `worker` agent. Parallel built-in `worker` subagents require no dependency between target files.
5b. A built-in `worker` handoff must include `target_path` (allowed edit files), `change_spec` (requested change), `context_files` (reference files), `validation_command`, and `slice_budget` (file and LOC cap).
5c. If the built-in `worker` returns `status: blocked`, the main thread either implements directly or switches to split or replan.
5d. If the built-in `worker` returns `status: final`, the main thread performs shared-file integration such as barrel exports or route registration, then proceeds to focused validation.
5e. For parallel built-in `worker` subagents, use `isolation: worktree` with independent git worktrees, then have the main thread integrate the resulting diffs.
5f. `multi-work` is optional. Consider it only when the approved slice is still large, can be expressed as 2 or more independent work units, each unit has a clear acceptance and merge boundary, and shared-file edits plus final validation remain with the main thread or integrator.
6. Use `browser-explorer` only when browser reproduction or visual evidence is needed. The handoff must include `target URL or Electron entry`, `scenario checklist`, and `evidence checklist`.
7. The main thread runs focused validation. The default is `one target-specific validation + one low-cost check`.
8. If validation passes, commit the change and update `STATUS.md` with a manager-facing summary.
9. Default single-slice mode stops after 1 slice. Run-to-boundary mode repeats the same loop until a stop or replan condition is hit.

## Guardrails

- Do not implement outside bundle documents.
- If `validation_gate: blocking` still has blocking issues, do not begin implementation.
- If `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, or project implementation rules are unresolved, do not begin implementation.
- If `delivery_strategy=ui-first`, do not skip or merge the `SLICE-1 -> SLICE-2 -> SLICE-3+` order, and do not mix real API or integration diff into early UI slices.
- Preserve the `slice implementation -> main focused validation -> commit` order.
- The default for hybrid mode is `small slices + run-to-boundary`.
- If the slice budget exceeds the small-slice guardrail (`repo-tracked files 3 or fewer`, net diff around `150 LOC`), fall back to `split/replan before execution`.
- If focused validation fails, do not commit and record the slice failure.
- If docs or other SSOT files change, finish the required sync and `--check` runs before exit.
- In `csv-fanout`, row workers may create or edit files only at `target_path`. They must not modify shared files directly.
- Built-in `worker` subagents do not edit files outside `target_path`. Shared files are integrated by the main thread.
- Built-in `worker` subagents do not perform git commit. Commit stays main-thread only.
- Do not let parallel built-in `worker` subagents edit the same file concurrently. If file-boundary conflicts are detected, switch back to sequential execution.
- Integrator-only files listed in `MERGE_POLICY.md` may be edited only by the integrator role.
- In non-Codex environments such as Claude Code, `csv-fanout` and `hybrid` automatically fall back to sequential `keep-local` execution.
- Do not treat `multi-work` as a required lifecycle step. It is an optional orchestration pattern only, and `csv-fanout`, built-in `worker` delegation, or `split/replan` remain the default fit checks.

## References

- Detailed execution rules, validation fallback, and STATUS contract: `references/execution-rules.md`
- Optional orchestration pattern for large approved slices with independent work units: `skills/multi-work/references/routing-contract.md`

## Validation

- Prefer validation commands from `EXECUTION_PLAN.md`.
- Use repo-aware fallback only when the documented validation command is empty.
- If you changed SSOT such as `skills` or `agent-registry`, run the matching sync plus `--check`.
- If you changed `skills`, include `python3 scripts/sync_skills_index.py --check`.
- If you changed `agent-registry`, include `python3 scripts/sync_agents.py --check`.
