# Plan Continuity Rules

Read this file only when deciding whether to reuse an existing task or create a new one.
The default principle is the continuity gate. Reuse is the exception; creating a new task is the default.
Compare new tasks through `task.yaml`, and compare legacy tasks through `PLAN.md` only as a fallback.

## Comparison Matrix

| Signal | Reuse existing | Create new |
| --- | --- | --- |
| Goal | same user outcome | create a new task when the goal differs |
| Success criteria | same `task.yaml.success_criteria` | create a new task when they differ |
| Work type | same `feature`/`bugfix`/`refactor`/`migration`/`prototype`/`ops` | create a new task when they differ |
| Impact flags | same core impact flags | create a new task when they differ |
| Required docs | same bundle shape after bootstrap-supplement normalization | create a new task when they still differ after normalization |
| Major boundaries | same `task.yaml.major_boundaries` | create a new task when they differ |
| Delivery strategy | same `task.yaml.delivery_strategy` | create a new task when they differ |
| Execution topology | same `task.yaml.execution_topology` | create a new task when they differ |
| Candidate count | exactly 1 | ambiguous case when there are 2 or more |

## Bootstrap Supplement Normalization

Do not treat the following post-design bootstrap additions as task-identity differences during continuity comparison.

- `IMPLEMENTATION_CONTRACT.md` inside `required_docs`
- `source_of_truth.implementation = IMPLEMENTATION_CONTRACT.md`

That means `required_docs` comparison uses the normalized set with bootstrap supplements removed.
`source_of_truth` comparison is not an identity signal; the optional `implementation` pointer does not break continuity.

## Decision Rules

1. If the user specifies a path directly, use that path.
2. Even without explicit continuation language, apply the continuity gate if related tasks are visible.
3. If a new bundle candidate exists, prefer `task.yaml`.
4. Use legacy `PLAN.md` only as a fallback comparison target when there is no new bundle candidate.
5. Choose `reuse-existing` only when there is exactly 1 new-bundle candidate whose `goal + success_criteria + work_type + impact_flags + normalized required_docs + major_boundaries + delivery_strategy` all match.
6. When updating an existing bundle through `reuse-existing`, preserve existing `IMPLEMENTATION_CONTRACT.md` and `source_of_truth.implementation` as bootstrap supplements.
7. Record `bootstrap supplement preserved` in `Task continuity` when it applies.
8. If any comparison signal differs, choose `create-new`.
9. If there are 2 or more candidates, do not auto-select and record it under `Need user decision`.

## Row-level Continuity (csv-fanout)

When updating a `csv-fanout` task, preserve row-level continuity for the existing work-items CSV.

- Existing `row_id` remains valid with no change -> skip (do not re-run completed rows).
- Existing `row_id` has changed acceptance criteria or `target_path` -> re-execute.
- New `row_id` was added -> append (run it in addition to existing results).
- Existing `row_id` was removed -> superseded (preserve the result, do not re-run).
- `execution_topology` itself changed (for example `keep-local -> csv-fanout`) -> creating a new task is the default.

## Examples

### Reuse existing

- The current request breaks the existing goal into smaller parts or only sharpens the acceptance criteria.
- Work type, impact flags, required docs, `success_criteria`, and `major_boundaries` stay the same.
- If the only difference is `IMPLEMENTATION_CONTRACT.md` and `source_of_truth.implementation` added by post-design bootstrap, treat it as the same task.

### Create new

- The goal is similar, but the success criteria differ.
- The domain is the same, but the change boundary moved from API to UI.
- The existing task is `delivery_strategy=standard`, but the new request needs `ui-first` decomposition.
- The existing task is a refactor, but the new request is a bugfix.
- The existing bundle only needed `PRD + ACCEPTANCE`, but the new request needs `UX_SPEC + TECH_SPEC + ADRs`.

### Ambiguous case

- There are 2 or more related unfinished tasks.
- Record comparison evidence in `Task continuity` and do not auto-reuse before user confirmation.
