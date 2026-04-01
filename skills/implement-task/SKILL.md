---
name: implement-task
description: >
  Execute the next approved slice from task.yaml bundles. Invoke only when
  the user explicitly writes "implement-task" or "$implement-task". Reads
  the bundle, selects the next slice, and hands off to `$parallel-workflow`
  for 3-CSV execution. Owns task selection, STATUS.md updates, and commit.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Implement Task

Select the next execution slice from an approved task bundle and hand off
to `$parallel-workflow` for 3-CSV execution.

## Trigger

- Invoke only when the user explicitly writes the exact skill name `implement-task` or `$implement-task`.

## Required Inputs

- bundle: `task.yaml`, `EXECUTION_PLAN.md`, `STATUS.md`
- if `task.yaml.agent_orchestration` exists, read it before choosing the execution lane. New bundles should include it.
- if `delivery_strategy=ui-first`, also read `task.yaml.source_of_truth.ux = UX_SPEC.md`, `task.yaml.source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `task.yaml.source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`
- if `task.yaml.source_of_truth.implementation` exists, read `IMPLEMENTATION_CONTRACT.md`
- if `execution_topology` is `csv-fanout` or `hybrid`, also read the static `task.yaml.orchestration` block
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
5. Read the current slice contract in `EXECUTION_PLAN.md` and hand off to `$parallel-workflow`. All bundle slices execute through the 3-CSV pipeline (info-collection → implementation → review).
6. After `$parallel-workflow` completes, commit the change and update `STATUS.md` with a manager-facing summary.
7. Default single-slice mode stops after 1 slice. Run-to-boundary mode repeats the same loop until a stop or replan condition is hit.

## Guardrails (pre-handoff gates)

These are checked before handing off to `$parallel-workflow`. If any gate
fails, stop and do not hand off.
- If `validation_gate: blocking` still has blocking issues, do not begin implementation.
- If `$bootstrap-project-rules`, `IMPLEMENTATION_CONTRACT.md`, or project implementation rules are unresolved, do not begin implementation.
- If `delivery_strategy=ui-first`, do not skip or merge the `SLICE-1 -> SLICE-2 -> SLICE-3+` order.
- If the slice budget exceeds the small-slice guardrail (`repo-tracked files 3 or fewer`, net diff around `150 LOC`), fall back to `split/replan before execution`.
- If focused validation fails, do not commit and record the slice failure.
- If docs or other SSOT files change, finish the required sync and `--check` runs before exit.

## References

- Detailed execution rules, validation fallback, and STATUS contract: `references/execution-rules.md`
- `$parallel-workflow` delegates to `$multi-work` for routing when needed.

## Validation

- Prefer validation commands from `EXECUTION_PLAN.md`.
- Use repo-aware fallback only when the documented validation command is empty.
- If you changed SSOT such as `skills` or `agent-registry`, run the matching sync plus `--check`.
- If you changed `skills`, include `python3 scripts/sync_skills_index.py --check`.
- If you changed `agent-registry`, include `python3 scripts/sync_agents.py --check`.
