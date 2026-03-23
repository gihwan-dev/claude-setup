---
name: design-task
description: >
  Large or ambiguous non-trivial task planning skill. Invoke only when the user
  explicitly writes `design-task` or `$design-task`. Build or update a
  tasks/{task-path}/task.yaml bundle via a continuity gate, derive
  `delivery_strategy`, and record `agent_orchestration` plus slice-level
  orchestration for bundle-based planning.
---

# Workflow: Design Task

## Goal

Turn the user request into a long-running task bundle, decide whether an existing task should be reused through the continuity gate, and create or update the document set centered on `tasks/<task-path>/task.yaml`.
Do not modify code during the design phase.
For greenfield or new-project work, a `$bootstrap-project-rules` handoff may be required before implementation.

## Hard Rules

- Do not edit code, config, or test files.
- Perform read-only exploration only.
- New task output is always a flat `tasks/<task-path>/` bundle.
- Do not create `PLAN.md` for new tasks.
- Record the `quality preflight` result as either `keep-local` or `orchestrated-task`.
- If the result is `keep-local`, return to the existing fast, deep-solo, or delegated lanes instead of starting long-running planning here.
- Reusing an existing task is the exception. Creating a new task is the default.
- If there are 2 or more candidates, do not auto-reuse. Record that user confirmation is required in `Task continuity`.
- In the continuity gate, normalize post-design bootstrap supplements (`IMPLEMENTATION_CONTRACT.md`, `source_of_truth.implementation`) and do not treat them as task-identity differences.
- On the `reuse-existing` path, preserve any existing bootstrap supplement instead of deleting it.
- `task.yaml.delivery_strategy` is required and only `standard` or `ui-first` is allowed.
- If `work_type` is one of `feature`, `prototype`, `refactor`, or `bugfix`, and `impact_flags` includes `ui_surface_changed` or `workflow_changed`, force `delivery_strategy=ui-first`.
- If `delivery_strategy=ui-first`, lock `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/` as the UX source of truth and preserve the slice order `UI -> local state/mock -> real API/integration`.
- If `delivery_strategy=ui-first`, auto-run `reference-pack` first to fill `DESIGN_REFERENCES/`, then let `figma-less-ui-design` author the `UI Planning Packet` in `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`. Preserve the exact section order for `UX_SPEC.md`: `Goal/Audience/Platform`, `30-Second Understanding Checklist`, `Visual Direction + Anti-goals`, `Reference Pack (adopt/avoid)`, `Glossary + Object Model`, `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`, `Implementation Prompt/Handoff`. Preserve the exact section order for `UX_BEHAVIOR_ACCESSIBILITY.md`: `Interaction Model`, `Keyboard + Focus Contract`, `Accessibility Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, `Microcopy + Information Expression Rules`, `Task-based Approval Criteria`.
- If an existing design system, shipped UI, brand guide, or Figma exists, record `reuse + delta` in the `UI Planning Packet` instead of proposing net-new style work.
- In greenfield or new-project planning, if repository-level implementation rules do not exist yet, leave a blocking `$bootstrap-project-rules` issue in `SPEC_VALIDATION.md`.
- For existing TS, JS, or React code, include structure preflight in quality preflight: target file role, expected post-change LOC, and whether split-first is needed.
- If the split-first trigger is on, forbid plans that assume target-file append and create the decomposition proposal first.
- Every execution slice must include change boundary, expected file count, validation owner, focused validation plan, and stop or replan conditions.
- Every new or updated task bundle must include `task.yaml.agent_orchestration`. Default to `strategy=manager` and `main_thread_role=synthesize-control-only`.
- In manager mode, the main thread only synthesizes bundle docs and structured helper results. Code reads or writes, shared-file integration, and validation execution belong to the designated execution roles.
- Every execution slice must also include a `split decision` plus a target-file append forbidden trigger.
- Every execution slice must include orchestration fields: `Orchestration`, `Preflight helpers`, `Implementation owner`, `Integration owner`, `Validation owner`, `Allowed main-thread actions`, `Focused validation plan`, and `Stop / Replan trigger`.
- The default slice guardrail is a small slice: `repo-tracked files 3 or fewer`, net diff around `150 LOC`. Anything larger must fall back to `split/replan before execution`.
- Do not create giant mixed slices that bundle common refactoring, multi-screen replacement, wholesale test updates, and static scans together.
- `execution_topology` is optional and defaults to `keep-local`. Allowed values: `keep-local`, `csv-fanout`, `hybrid`.
- `agent_orchestration` is required for new or updated bundles. It must include `strategy`, `main_thread_role`, `planning_helpers`, `execution_roles`, `context_policy`, `fallback_policy`, and `review_policy`.
- Choose `csv-fanout` only when all 5 conditions hold: (1) the repeat unit is clear, (2) each unit has independent acceptance criteria, (3) inter-unit dependencies are sparse, (4) the output schema is fixed, and (5) the merge boundary is clear.
- If `csv-fanout` or `hybrid` is used, add the `orchestration` block to `task.yaml`.
- If `csv-fanout` is used, add `GLOBAL_CONTEXT.md`, `work-items/*.csv`, and `MERGE_POLICY.md` to the bundle and include them in `required_docs`.
- Row workers may create or edit files only at `target_path` and may not modify shared files. Shared files are integrator-only.
- For Figma-related CSV schemas, use the separate `figma-codex-pipeline` skill.

## Required References

- Read `${SKILL_DIR}/references/plan-continuity-rules.md` only when a continuity gate is needed.
- Read `${SKILL_DIR}/references/task-bundle-rules.md` for document-selection rules and gate rules for new bundles.
- Read `${SKILL_DIR}/references/planning-role-cards.md` only when a planning-role fallback overlay is needed.
- If `delivery_strategy=ui-first`, read `skills/reference-pack/SKILL.md` first and apply the task-local reference contract.
- If the plan is UI-first without Figma or the UX packet is weak, read `skills/figma-less-ui-design/SKILL.md` and reuse the two-document packet contract.

## Inputs

- user request
- codebase read-only exploration results
- user-specified documents or paths
- existing `tasks/<task-path>/task.yaml`, `README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, `STATUS.md`

## Task Path Selection

1. If the user specifies a path directly, use it without running the continuity gate.
2. If the request contains continuation language such as `continue`, `update`, `replan`, or `continue the existing plan`, compare existing task candidates first.
3. If a new bundle candidate exists, apply the continuity gate using `task.yaml`.
4. Reuse a task path only when there is exactly 1 candidate whose `goal + success_criteria + work_type + impact_flags + normalized required_docs + major_boundaries + delivery_strategy + agent_orchestration.strategy + agent_orchestration.main_thread_role` all match.
5. If any of those differ, or the judgment is `goal differs`, create a new flat task path.
6. Use the current goal normalized to hyphen-case as the base slug for a new path.
7. If the base slug collides, add a suffix that shows the current planning focus first, such as `-task-identity`, `-plan-split`, `-api`, or `-ui`.
8. Only if the focus suffix also collides, use `-v2` as the final fallback.

## Workflow

1. Extract the request goal, constraints, and success criteria.
2. Investigate related code, documents, and existing `tasks/` docs in read-only mode, and collect evidence for quality preflight.
3. If this is existing code work, run structure preflight and record whether `split-first` is needed.
4. Record the quality-preflight verdict and the follow-up route.
5. If the verdict is not `orchestrated-task`, stop here and return to the existing lane.
6. If continuation language or related task traces exist, run the continuity gate.
7. In `Task continuity`, record `decision`, `compared tasks`, `reason`, and `chosen task path`. Also record bootstrap-supplement normalization or preservation when it applies.
8. Decide `work_type` as one of `feature`, `bugfix`, `refactor`, `migration`, `prototype`, or `ops`.
9. Fix the core `impact_flags`, then decide `delivery_strategy` as `standard` or `ui-first`.
9a. Decide `execution_topology`. Use `csv-fanout` when all 5 fan-out conditions hold, `hybrid` when only part of them hold, and otherwise `keep-local` (default).
9b. Add `agent_orchestration` to `task.yaml`. Default it to `strategy=manager`, `main_thread_role=synthesize-control-only`, helper-driven planning, bounded execution roles, bundle-doc plus structured-result context policy, `split-replan` fallback, and explicit `multi-review` review boundary.
9c. If `csv-fanout` or `hybrid` is selected, add the `orchestration` block (`row_unit`, `batch_mode`, `shared_context_files`, `roles`, `csv`, `merge_policy`) to `task.yaml`.
9d. If `csv-fanout` is selected, create `GLOBAL_CONTEXT.md`, the `work-items/` directory, and `MERGE_POLICY.md`, then add them to `required_docs`.
10. Decide `required_docs` using `${SKILL_DIR}/references/task-bundle-rules.md`. If the path is `reuse-existing` and the bundle already contains a bootstrap supplement, preserve `IMPLEMENTATION_CONTRACT.md`.
11. Write `task.yaml` as the machine entry point. If the path is `reuse-existing` and the bundle already has `source_of_truth.implementation`, preserve that optional pointer too.
12. Write `README.md` as the human-facing landing document.
13. If `delivery_strategy=ui-first`, auto-run `reference-pack` first to fill `DESIGN_REFERENCES/`, then lock `source_of_truth.ux = UX_SPEC.md`, `source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`. Do not create integration slices until `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md` are in place.
14. In `EXECUTION_PLAN.md`, preserve the level-1 sections `Execution slices`, `Verification`, and `Stop / Replan conditions`, then describe bounded slices, orchestration ownership, focused validation, and split decisions.
14a. For every slice, record `Orchestration`, `Preflight helpers`, `Implementation owner`, `Integration owner`, `Validation owner`, `Allowed main-thread actions`, `Focused validation plan`, and `Stop / Replan trigger`.
14b. If `csv-fanout` is used, add a fan-out spec to each slice in `EXECUTION_PLAN.md`: CSV source, concurrency, batch mode, and row-worker scope.
15. If `delivery_strategy=ui-first`, fix `SLICE-1` as static or visual UI, `SLICE-2` as local state or mock work, and `SLICE-3+` as real API or integration. Explicitly forbid real API or integration work in `SLICE-1` and `SLICE-2`.
16. Always create `SPEC_VALIDATION.md` and record a `blocking` or `advisory` verdict. If `delivery_strategy=ui-first` still lacks UX docs, a finished reference pack, or defined 30-second checklist, glossary, interaction, accessibility, live-update, degradation, and task-based approval sections, record them in `Blocking issues`. If the repo lacks baseline implementation rules for greenfield or new-project work, record a `$bootstrap-project-rules` requirement in `Blocking issues`.
17. Create `STATUS.md` from the initial template, setting `Current slice` to `Not started.` and `Next slice` to `SLICE-1`.
18. Reflect `source_of_truth` and traceability IDs in the documents. Leave handoff notes in task `README.md` and `SPEC_VALIDATION.md` that `source_of_truth.implementation = IMPLEMENTATION_CONTRACT.md` may be added after post-design bootstrap.
19. Keep bundle documents as the only planning output.

## Multi-Agent Usage

Read-only research, exploration, and browser reproduction always belong to helpers.
The main thread only synthesizes their results.
For manager-mode planning, record the resulting orchestration choice in `task.yaml.agent_orchestration` and keep `EXECUTION_PLAN.md` aligned with that ownership model.

### Agent Usage

For quality preflight on existing TS, JS, or React code, default to the built-in `explorer`.
Use the built-in `explorer` for repo read-only discovery, `web-researcher` for external research, and `browser-explorer` for browser reproduction.
When structural smells or `split-first` risk appears, add `structure-reviewer` and `test-engineer` so decomposition boundaries are clarified first.
When public or shared boundary risk appears, fan out to `architecture-reviewer` first to lock the boundary decision.
For AI or agent workflow planning, start with `web-researcher` and prioritize official vendor docs such as OpenAI and Anthropic.
Keep planning fan-out limited to independent lenses instead of broad multi-agent sprawl.
If helpers are unavailable, report blocked instead of replacing them with direct main-thread research.
When a planning-role-card overlay is needed, use the built-in `explorer` together with `${SKILL_DIR}/references/planning-role-cards.md`.
Use `architecture-reviewer` for boundary or module-impact checks, `type-specialist` for public type or contract impact, and `test-engineer` for deriving validation scenarios.

## Required Bundle Content

Every new task bundle includes at least these 5 documents.

- `task.yaml`
- `README.md`
- `EXECUTION_PLAN.md`
- `SPEC_VALIDATION.md`
- `STATUS.md`

Add the following when the topology is `csv-fanout` or `hybrid`.

- `GLOBAL_CONTEXT.md`
- `MERGE_POLICY.md`

Add the following when the topology is `csv-fanout`.

- `work-items/` (containing at least 1 `.csv` file)

Add specialized docs such as `PRD.md`, `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `TECH_SPEC.md`, `BUG_REPORT.md`, `ROOT_CAUSE.md`, `MIGRATION.md`, `RUNBOOK.md`, and `DESIGN_REFERENCES/` according to the doc-selection matrix in `${SKILL_DIR}/references/task-bundle-rules.md`.

## Required Sections / Fields

- `SPEC_VALIDATION.md` keeps the order `Requirement coverage`, `UX/state gaps`, `Architecture/operability risks`, `Slice dependency risks`, `Blocking issues`, `Proceed verdict`.
- `STATUS.md` keeps `Current slice`, `Done`, `Decisions made during implementation`, `Verification results`, `Known issues / residual risk`, `Next slice`.
- `task.yaml` must contain `task`, `goal`, `success_criteria`, `major_boundaries`, `work_type`, `impact_flags`, `required_docs`, `source_of_truth`, `ids`, `delivery_strategy`, `agent_orchestration`, `validation_gate`, and `current_phase`.
- `task.yaml` must contain `agent_orchestration`.
- `execution_topology` is optional and may be `keep-local` (default), `csv-fanout`, or `hybrid`.
- `agent_orchestration` must include `strategy`, `main_thread_role`, `planning_helpers`, `execution_roles`, `context_policy`, `fallback_policy`, and `review_policy`.
- If `csv-fanout` or `hybrid` is used, the `orchestration` block is required and must include `row_unit`, `batch_mode`, `shared_context_files`, `roles`, `csv`, and `merge_policy`.
- Post-design bootstrap may add `IMPLEMENTATION_CONTRACT.md` to `required_docs` and `source_of_truth`.
- `EXECUTION_PLAN.md` keeps the order `Execution slices`, `Verification`, `Stop / Replan conditions`.

## Output Quality Checklist

- Did `Task continuity` capture the continuity-gate result and the reason for creating or reusing a task?
- Did the continuity comparison normalize `IMPLEMENTATION_CONTRACT.md` and `source_of_truth.implementation` instead of treating them as identity differences?
- On the `reuse-existing` path, were existing bootstrap supplements preserved and recorded as preserved in `Task continuity`?
- Are `work_type` and the core `impact_flags` fixed?
- Is `delivery_strategy` fixed and included in the continuity comparison basis?
- Does `agent_orchestration` exist, and does it lock `strategy=manager` plus `main_thread_role=synthesize-control-only` unless a documented exception applies?
- Do `required_docs` match the real bundle structure?
- Is the `SPEC_VALIDATION.md` verdict clearly `blocking` or `advisory`?
- For greenfield or new-project work, is the `$bootstrap-project-rules` handoff requirement clear in `Blocking issues`?
- Does each slice include orchestration ownership, change boundary, file budget, validation owner, and a stop or replan trigger?
- Does each slice include a `split decision` and a target-file append forbidden trigger?
- If `delivery_strategy=ui-first`, are the `SLICE-1 / 2 / 3+` order and the real API or integration prohibition explicit?
- If `delivery_strategy=ui-first`, did `reference-pack` fill `DESIGN_REFERENCES/`, did `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md` preserve exact order, and did the docs record `reuse + delta` when an existing style source exists?
- If `execution_topology=csv-fanout`, is the reasoning for the 5-condition judgment documented?
- If `csv-fanout` is used, are `GLOBAL_CONTEXT.md`, `MERGE_POLICY.md`, and `work-items/*.csv` included in the bundle?
- If `csv-fanout` is used, does `MERGE_POLICY.md` explicitly forbid shared-file edits by row workers?
- Do traceability IDs follow the `REQ`, `SCR`, `FLOW`, `ADR`, `AC`, `SLICE`, and `RISK` scheme?
