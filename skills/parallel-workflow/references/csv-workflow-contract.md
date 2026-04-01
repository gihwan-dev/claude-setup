# Parallel Workflow CSV Contract

This reference defines the runtime artifacts owned by `parallel-workflow`.

## Runtime Root

All runtime artifacts live under:

`runs/parallel-workflow/<slice-id>/`

Required files:

- `Documentation.md`
- `info-collection.csv`
- `implementation.csv`
- `review.csv`

These files are runtime artifacts, not design-time bundle docs.

## `Documentation.md`

Keep this file short and durable. It should capture:

- active slice and goal
- locked routing contract
- cross-row blockers
- shared-file decisions
- fallback reasons
- final execution summary

Do not dump raw logs or long helper transcripts here.

## `info-collection.csv`

Create this first and always populate these columns:

| Column | Required | Notes |
|---|---|---|
| `row_id` | Y | Stable per information row |
| `category` | Y | Information category or lane |
| `question` | Y | Concrete question to answer |
| `scope_boundary` | Y | Exact boundary for that row |
| `assigned_agent_type` | Y | Locked helper type |
| `depends_on` | N | Comma-separated `row_id` list |
| `status` | Y | `pending`, `running`, `done`, `blocked`, or `skipped` |
| `last_error` | N | Last failure reason |
| `result_summary` | N | Short result summary |

Use CSV-1 to close routing, blockers, and row decomposition.

## `implementation.csv`

Create this file up front as a skeleton, but do not finalize rows until
`info-collection.csv` completes.

Required columns:

| Column | Required | Notes |
|---|---|---|
| `row_id` | Y | Stable implementation row id |
| `change_group_id` | Y | Shared-file collision group |
| `target_path` | Y | Primary file boundary |
| `change_goal` | Y | Exact implementation goal |
| `assigned_agent_type` | Y | Locked executor type |
| `shared_file_touch` | Y | `Y` or `N` |
| `parallelizable` | Y | `true` or `false` |
| `execution_mode` | Y | `parallel`, `single-lane`, or `blocked` |
| `validation_command` | N | Row-local validation command |
| `fallback_reason` | N | Why single-lane or blocked was chosen |
| `status` | Y | `pending`, `running`, `done`, `blocked`, or `skipped` |
| `last_error` | N | Last failure reason |

Rules:

- `shared_file_touch=Y` may not run as independent parallel writes.
- Rows sharing a `change_group_id` must use a single lane.
- If parallel execution is not safe, keep the row in `execution_mode=single-lane`
  and explain why in `fallback_reason`.

## `review.csv`

Create this after implementation rows are known.

Required columns:

| Column | Required | Notes |
|---|---|---|
| `row_id` | Y | Stable review row id |
| `target_row_id` | Y | `implementation.csv` row id |
| `review_focus` | Y | What the reviewer checks |
| `assigned_agent_type` | Y | Locked reviewer type |
| `severity_gate` | Y | `advisory`, `critical`, or `blocker` |
| `fix_owner` | Y | `parallel-workflow`, `main-thread`, or explicit lane owner |
| `auto_fix` | Y | `true` or `false` |
| `validation_command` | N | Validation to rerun after a fix |
| `status` | Y | `pending`, `running`, `done`, `blocked`, or `skipped` |
| `last_error` | N | Last failure reason |
| `result_summary` | N | Short review result |

Auto-fix rules:

- Default to `false`.
- Set `auto_fix=true` only when `severity_gate` is `critical` or `blocker`,
  the validation command is row-local, and the fix boundary stays small.
- Leave advisory findings review-only.
