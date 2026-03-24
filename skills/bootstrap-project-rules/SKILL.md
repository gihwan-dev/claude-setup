---
name: bootstrap-project-rules
description: >
  Post-design bootstrap workflow for greenfield or newly shaped work. Use after
  design-task and before implement-task when the task bundle is ready but the repo
  still needs implementation rules. Creates ENGINEERING_RULES.md and
  IMPLEMENTATION_CONTRACT.md. Do not use before design-task completes or when
  implementation rules already exist.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Workflow: Bootstrap Project Rules

## Goal

Lock the selected task bundle into an implementation-ready contract.
Read the `design-task` outputs, create or update the repo baseline
`docs/ai/ENGINEERING_RULES.md` and the task supplement
`tasks/<task-path>/IMPLEMENTATION_CONTRACT.md`, and align the managed link section in the
root `README.md` when needed.
Keep `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, and `DESIGN_REFERENCES/manifest.json`
as the UX source of truth; bootstrap should lock only the implementation stack, tooling,
and boundaries.

## Hard Rules

- Do not change code, config, tests, or install packages. Update only documentation and agent-memory contracts.
- Use this only after `design-task`. If the bundle has no `task.yaml`, do not start.
- If there is more than one path candidate, do not auto-select. Stop and ask the user to confirm.
- Start from current repo facts first: manifests, config, existing docs, and existing AGENTS/CLAUDE files. Ask only short questions for hard-to-reverse decisions.
- The dependency policy must always be recorded under the three categories `Locked now`, `Deferred`, and `Banned/Avoid`.
- `Locked now` must include runtime/language, framework, package manager, lint/format/typecheck/test stack, the default state/data-fetching strategy, the default styling/design-system direction, and folder/module boundaries.
- `Locked now` must also include the styling stack, component source, Storybook/screenshot tooling, and token source path.
- If an optional library is not yet fixed by the current documentation scope, do not approve it up front. Leave it under `Deferred` and record a re-decision trigger for each item.
- Record repo-level implementation rules only in `docs/ai/ENGINEERING_RULES.md`.
- Do not create or update a root global memory markdown file.
- Keep `README.md` human-facing. Add only a short `AI Workflow` or `Engineering Rules` link section.
- Do not overwrite the entire existing `README.md`. Update only the managed section.
- Use the following lines as the `README.md` managed-section markers.
  - `<!-- bootstrap-project-rules:start -->`
  - `<!-- bootstrap-project-rules:end -->`
- If `README.md` does not exist, do not create a long new README. Leave only an advisory and write the AI docs.
- If `SPEC_VALIDATION.md` still has blockers beyond bootstrap-specific blocking issues, do not resolve them on your own.
- If a core architecture decision is still unresolved, you may leave `IMPLEMENTATION_CONTRACT.md` as a partial draft, but do not claim the bootstrap blocker is resolved.
- Keep UX ownership in `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`; bootstrap must not redefine visual direction or behavior contracts.
- Use `docs/ai/ENGINEERING_RULES.md` as the single source of truth for the repo baseline.
- Use `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md` as the single source of truth for the task supplement.
- Keep `README.md` focused on human-readable purpose, run instructions, and doc map; AI docs should be linked only.
- Update the root README only inside the managed section. If the managed section does not exist, append it to the end. Preserve all user-authored text outside the managed section.

## Required References

- Read `${SKILL_DIR}/references/decision-catalog.md` only when you need the decision categories and defer criteria.
- Read `${SKILL_DIR}/references/doc-templates.md` for the document skeleton and managed section format.

## Inputs

- The selected `tasks/<task-path>/task.yaml`
- The same task's `README.md`, `SPEC_VALIDATION.md`, and `EXECUTION_PLAN.md`
- Any existing `PRD.md`, `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `TECH_SPEC.md`, `ADRs/`, and `ACCEPTANCE.feature`
- The repo-root `README.md`
- Manifests/config such as `package.json`, lockfiles, `pyproject.toml`, `tsconfig.json`, `eslint`, formatter, and CI/workflow files

## Task Selection Rules

1. If the user specifies a slug/path directly, use that task.
2. If no path is given, build the active bundle candidates.
3. Auto-select only when there is exactly one candidate.
4. If there are two or more candidates, stop and ask the user to confirm instead of auto-running.
5. Apply this only to bundle-based tasks.

## Workflow

1. Determine the task path and bundle mode.
2. Read `task.yaml`, `SPEC_VALIDATION.md`, `README.md`, and the source-of-truth design docs, then extract the uncertainties that affect implementation. If `UX_SPEC.md` exists, check checklist/layout/token/screen-flow first. If `UX_BEHAVIOR_ACCESSIBILITY.md` exists, check interaction/a11y/live/state/approval contracts first.
3. Read the repo-root docs and manifests/config and classify already-fixed facts as `Fact`.
4. Classify decisions using `${SKILL_DIR}/references/decision-catalog.md`.
   - `Locked now`
   - `Deferred`
   - `Banned/Avoid`
5. Narrow follow-up questions to only the `Locked now` items that cannot be confirmed from repo exploration alone.
6. Write or update `docs/ai/ENGINEERING_RULES.md`. Lock the styling stack, component source, Storybook/screenshot tooling, and token source path as implementation-facing rules.
7. Write or update `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md`. Preserve ownership in `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`, and add only the implementation guardrails each slice needs to read.
8. Add `IMPLEMENTATION_CONTRACT.md` to `task.yaml.required_docs` and record `source_of_truth.implementation = IMPLEMENTATION_CONTRACT.md`.
9. Strengthen the task `README.md` document map and key decisions from the implementation-contract point of view.
10. If it exists, update the managed section in the root `README.md`.
11. Resolve only the blocking issues in `SPEC_VALIDATION.md` that meet all of the following conditions.
    - They require greenfield/new-project bootstrap.
    - They explicitly require running `$bootstrap-project-rules`.
    - They are actually resolved by the current documentation.
12. If other blockers remain, keep the `Proceed verdict` as-is and state that implementation still cannot start after bootstrap.
13. Do not start implementation or install packages. Leave only the `implement-task` handoff.

## Handoff Rules

- After bootstrap succeeds, the next step is `implement-task`.
- If unresolved architecture decisions, missing validation commands, or conflicting sources of truth remain, keep the bootstrap blocker and do not hand off.
- Do not auto-approve `Deferred` items during implementation slices. Re-decide them only when the documented trigger is met.

## Output Quality Checklist

- Does `docs/ai/ENGINEERING_RULES.md` follow the fixed section order?
- Does `IMPLEMENTATION_CONTRACT.md` separate task-bundle inputs from task-specific decisions?
- Are `Locked now`, `Deferred`, and `Banned/Avoid` all filled in, with re-decision triggers for each `Deferred` item?
- Were `task.yaml.required_docs` and `source_of_truth.implementation` updated?
- Were the bootstrap-related blocking issues resolved, or was the reason they remain unresolved recorded?
- Did the work leave only documentation contracts, without implementation or package installation?
