# Task Bundle Rules

Read this file only when `design-task` creates or updates a new long-running task.
The goal is to fix the task bundle structure by separating human-facing docs from the machine entry point instead of relying on a single `PLAN.md`.

## Core Docs

Create the following documents for every new task bundle.

- `task.yaml`
- `README.md`
- `EXECUTION_PLAN.md`
- `SPEC_VALIDATION.md`
- `STATUS.md`

`task.yaml` is the machine entry point.
`README.md` is the human-facing landing document.
Do not create `PLAN.md` for new tasks.

## `task.yaml`

Required keys:

- `task`
- `goal`
- `success_criteria`
- `major_boundaries`
- `work_type`
- `impact_flags`
- `required_docs`
- `source_of_truth`
- `ids`
- `delivery_strategy`
- `agent_orchestration`
- `validation_gate`
- `current_phase`

Optional keys:


`required_docs` lists the real bundle documents and directories excluding `task.yaml` itself.
`source_of_truth` points only to real file paths.
`success_criteria` and `major_boundaries` are used directly in continuity-gate comparison.
`delivery_strategy` is also used directly in continuity-gate comparison.
`agent_orchestration` is required for new or updated bundles in this repo.
After post-design bootstrap, `IMPLEMENTATION_CONTRACT.md` may be added to `required_docs`,
and `source_of_truth.implementation` may appear as an optional pointer.
When updating an existing bundle via `reuse-existing`, preserve any bootstrap supplement that already exists.

`agent_orchestration` required keys:

- `strategy` — currently `manager`
- `main_thread_role` — currently `synthesize-control-only`
- `planning_helpers` — ordered helper list used during planning
- `execution_roles` — mapping of implementation/integration/validation responsibilities to helper or worker roles
- `context_policy` — short statement describing what the main thread may read
- `fallback_policy` — short statement describing what happens when an execution lane blocks
- `review_policy` — short statement describing review ownership and whether review is explicit or automatic

## Work Types

- `feature`
- `bugfix`
- `refactor`
- `migration`
- `prototype`
- `ops`

## Delivery Strategies

- `standard`
- `ui-first`

Derived rules:

- If `work_type` is `feature`, `prototype`, `refactor`, or `bugfix`, and `impact_flags` includes `ui_surface_changed` or `workflow_changed`, use `ui-first`
- Otherwise use `standard`
- Otherwise use `standard`
- For `ui-first`, run `reference-pack` first to fill `DESIGN_REFERENCES/`, then let `figma-less-ui-design` write `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`.
- If an existing design system, shipped UI, brand guide, or Figma exists, the packet records `reuse + delta` rather than inventing a new style.
- For `ui-first`, do not create integration slices until UX direction, behavior or accessibility or live-update contracts, and state or fixture strategy are defined.

## Execution

All slices execute through the 3-CSV pipeline (read → write → review) defined
in `implement-task/references/csv-execution-rules.md`. Runtime CSV artifacts
are not added to `required_docs`.

## UI Planning Packet (`UX_SPEC.md`)

If `delivery_strategy=ui-first`, `UX_SPEC.md` keeps the exact heading order below.

- `Goal/Audience/Platform`
- `30-Second Understanding Checklist`
- `Visual Direction + Anti-goals`
- `Reference Pack (adopt/avoid)`
- `Glossary + Object Model`
- `Layout/App-shell Contract`
- `Token + Primitive Contract`
- `Screen + Flow Coverage`
- `Implementation Prompt/Handoff`

## UX Behavior & Accessibility (`UX_BEHAVIOR_ACCESSIBILITY.md`)

If `delivery_strategy=ui-first`, `UX_BEHAVIOR_ACCESSIBILITY.md` keeps the exact heading order below.

- `Interaction Model`
- `Keyboard + Focus Contract`
- `Accessibility Contract`
- `Live Update Semantics`
- `State Matrix + Fixture Strategy`
- `Large-run Degradation Rules`
- `Microcopy + Information Expression Rules`
- `Task-based Approval Criteria`

## Reference Pack (`DESIGN_REFERENCES/`)

If `delivery_strategy=ui-first`, `DESIGN_REFERENCES/` includes the following.

- `shortlist.md`
- `manifest.json`
- `raw/`
- `curated/`

Additional rules:

- Auto-run the `reference-pack` advisory skill for every `ui-first` plan.
- Add `web-researcher`, `structure-reviewer`, and `architecture-reviewer` only when conditions justify them.
- `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`, `Interaction Model`, `Accessibility Contract`, and `Microcopy + Information Expression Rules` justify entering `SLICE-1`.
- `Keyboard + Focus Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, and `Task-based Approval Criteria` justify entering `SLICE-2`.
- Record `source_of_truth.ux = UX_SPEC.md`, `source_of_truth.ux_behavior = UX_BEHAVIOR_ACCESSIBILITY.md`, and `source_of_truth.design_references = DESIGN_REFERENCES/manifest.json`.

## Parallel Runtime Artifacts

## Runtime Artifacts

Runtime CSV artifacts (`info-collection.csv`, `implementation.csv`,
`review.csv`, `Documentation.md`) are created by `implement-task` at
execution time under `runs/<slice-id>/`. They are not added to
`required_docs`.

## Impact Flags

- `ui_surface_changed`
- `workflow_changed`
- `architecture_significant`
- `public_contract_changed`
- `data_contract_changed`
- `operability_changed`
- `high_user_risk`

## Traceability IDs

- `requirement_prefix: REQ`
- `screen_prefix: SCR`
- `flow_prefix: FLOW`
- `adr_prefix: ADR`
- `acceptance_prefix: AC`
- `slice_prefix: SLICE`
- `risk_prefix: RISK`

Cross-document linkage must use ID references, not copy-pasted prose.

## Doc Selection Matrix

### `feature`

Default docs:

- `PRD.md`
- `ACCEPTANCE.feature`

Additional rules:

- If `ui_surface_changed` or `workflow_changed` is present, add `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/`
- If any of `architecture_significant`, `public_contract_changed`, `data_contract_changed`, or `operability_changed` is present, add `TECH_SPEC.md`
- If `architecture_significant` is present, add `ADRs/`
- If `public_contract_changed` is present, the default contract doc is `openapi.yaml`
- If `data_contract_changed` is present, the default contract doc is `schema.json`

### `bugfix`

Default docs:

- `BUG_REPORT.md`
- `ROOT_CAUSE.md`
- `ACCEPTANCE.feature`

Additional rules:

- If any of `high_user_risk`, `public_contract_changed`, or `data_contract_changed` is present, add `REGRESSION.md`

### `refactor`

Default docs:

- `CURRENT_STATE.md`
- `TARGET_STATE.md`

Additional rules:

- If architecture, public, data, or operability flags are present, add `TECH_SPEC.md`
- If any of `ui_surface_changed`, `workflow_changed`, `public_contract_changed`, or `high_user_risk` is present, add `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/`, and `ACCEPTANCE.feature`

### `migration`

Default docs:

- `TECH_SPEC.md`
- `MIGRATION.md`
- `VERIFICATION.md`
- `ROLLBACK.md`

Additional rules:

- If `public_contract_changed` is present, add `openapi.yaml`
- If `data_contract_changed` is present, add `schema.json`

### `prototype`

Default docs:

- `PRD.md`
- `VERIFICATION.md`

Additional rules:

- If `ui_surface_changed` or `workflow_changed` is present, add `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/`
- If architecture, public, data, or operability flags are present, add `TECH_SPEC.md`
- If any of `public_contract_changed`, `data_contract_changed`, or `high_user_risk` is present, add `ACCEPTANCE.feature`

### `ops`

Default docs:

- `CHANGE_PLAN.md`
- `RUNBOOK.md`
- `ROLLBACK.md`
- `VERIFICATION.md`

## `SPEC_VALIDATION.md`

Always create this document and preserve the level-1 heading order below.

- `Requirement coverage`
- `UX/state gaps`
- `Architecture/operability risks`
- `Slice dependency risks`
- `Blocking issues`
- `Proceed verdict`

Gate rules:

- If any of `ui_surface_changed`, `workflow_changed`, `architecture_significant`, `public_contract_changed`, `data_contract_changed`, `operability_changed`, or `high_user_risk` is present, the verdict is `blocking`
- Even without those flags, if 3 or more design docs are required, the verdict is `blocking`
- Otherwise the verdict is `advisory`

Additional rules:

- If this is greenfield or new-project planning and baseline repo implementation rules (`docs/ai/ENGINEERING_RULES.md`) do not exist yet, leave a `$bootstrap-project-rules` requirement in `Blocking issues`.
- If `ui-first` is selected but any of `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, or `DESIGN_REFERENCES/manifest.json` is empty, or if the 30-second checklist, glossary, interaction, accessibility, live-update, degradation, or task-based approval sections are missing, record that in `Blocking issues`.
- When an existing shipped UI, Figma, or design system is clearly available, weak reference capture may be lowered to advisory, but the reason for that judgment must be recorded.
- Do not auto-clear this blocking issue during the design phase. Only mark it cleared after post-design bootstrap is complete.

## `EXECUTION_PLAN.md`

Preserve the level-1 heading order below.

- `Execution slices`
- `Verification`
- `Stop / Replan conditions`

Every slice inside `Execution slices` includes at least the fields below.

- Change boundary
- Expected files
- Execution skill (`implement-task` for all slices)
- Orchestration
- Preflight helpers
- Implementation owner
- Integration owner
- Validation owner
- Allowed main-thread actions
- Focused validation plan
- Stop / Replan trigger

For manager-mode bundles, `Allowed main-thread actions` should stay orchestration-only, such as bundle-doc synthesis, structured helper-result synthesis, handoff management, status updates, and commit coordination.

Additional rules for `delivery_strategy=ui-first`:

- `SLICE-1`: handle only static or visual UI, information architecture, copy, navigation, and visual shell. Real API or integration is forbidden.
- `SLICE-2`: handle only local interaction, mock data, and loading, empty, error, permission, responsive, and accessibility states. Real API or integration is forbidden.
- `SLICE-3+`: handle real API, backend, data contract, integration, and regression hardening.
- If `SLICE-1` is not approved or the `SLICE-2` state model is unresolved, block entry to the next slice through stop or replan.

## `README.md`

Keep it to one page.

- Goal
- Document map
- Key decisions
- Validation gate status
- Implementation slice order

If this is greenfield or new-project planning, leave the post-design bootstrap handoff in `Document map` or `Validation gate status`.
After bootstrap, `IMPLEMENTATION_CONTRACT.md` may be added to the document map.
If a bootstrap supplement was preserved on a `reuse-existing` path, record that preserved fact in `Task continuity` or `Key decisions`.

If `delivery_strategy=ui-first`, `Implementation slice order` must reflect the exact order `SLICE-1 -> SLICE-2 -> SLICE-3+`.

## `STATUS.md`

Create the initial template during the design phase.
Fix `Current slice` to `Not started.` and `Next slice` to `SLICE-1`.
