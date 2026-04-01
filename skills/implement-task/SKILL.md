---
name: implement-task
description: >
  Execute the next approved slice from task.yaml bundles. Invoke only when
  the user explicitly writes "implement-task" or "$implement-task". Reads
  the bundle, selects the next slice, and runs the 3-CSV pipeline
  (read → write → review). Owns task selection, STATUS.md updates, and commit.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Implement Task

Select the next execution slice from an approved task bundle and run
the 3-CSV pipeline (read → write → review) for each slice.

## Trigger

- Invoke only when the user explicitly writes the exact skill name `implement-task` or `$implement-task`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- if `task.yaml.agent_orchestration` exists, read it before choosing the execution lane. New bundles should include it.
- if `delivery_strategy=ui-first`, also read `task.yaml.source_of_truth.ux = UX_SPEC.md`, `task.yaml.source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `task.yaml.source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`
- if `task.yaml.source_of_truth.implementation` exists, read `IMPLEMENTATION_CONTRACT.md`
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
4. If `task.yaml.agent_orchestration` exists and `strategy=manager`, lock the manager lane before code work starts.
5. Read the current slice contract in `EXECUTION_PLAN.md`. Then read `${SKILL_DIR}/references/csv-execution-rules.md` and run the 3-CSV pipeline for the current slice. Runtime artifacts go under `runs/<slice-id>/`.
6. After the 3-CSV pipeline completes, commit the change and update `STATUS.md`.
7. Default single-slice mode stops after 1 slice. Run-to-boundary mode repeats the same loop until a stop or replan condition is hit.

## Guardrails

These are checked before starting the 3-CSV pipeline. If any gate fails,
stop before execution.
- If `validation_gate: blocking` still has blocking issues, do not begin implementation.
- If `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, or project implementation rules are unresolved, do not begin implementation.
- If `delivery_strategy=ui-first`, do not skip or merge the `SLICE-1 -> SLICE-2 -> SLICE-3+` order.
- If the slice budget exceeds the small-slice guardrail (`repo-tracked files 3 or fewer`, net diff around `150 LOC`), fall back to `split/replan before execution`.
- If focused validation fails, do not commit and record the slice failure.
- If docs or other SSOT files change, finish the required sync and `--check` runs before exit.

## References

- Detailed execution rules and STATUS contract: `references/execution-rules.md`
- 3-CSV execution pipeline: `${SKILL_DIR}/references/csv-execution-rules.md` (read and execute inline for each slice)

## Validation

- Prefer validation commands from `EXECUTION_PLAN.md`.
- Use repo-aware fallback only when the documented validation command is empty.
- If you changed SSOT such as `skills` or `agent-registry`, run the matching sync plus `--check`.
- If you changed `skills`, include `python3 scripts/sync_skills_index.py --check`.
- If you changed `agent-registry`, include `python3 scripts/sync_agents.py --check`.
