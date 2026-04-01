# Slice-level CSV Execution Rules

This reference defines the 3-CSV runtime pipeline that every bundle slice
must follow. Read this file before executing any slice.

## Runtime Root

All runtime artifacts live under:

`runs/<slice-id>/`

Create these 4 files for every slice:

- `Documentation.md` — durable runtime memory
- `info-collection.csv` — read phase ledger
- `implementation.csv` — write phase ledger
- `review.csv` — review phase ledger

## Documentation.md

Record: active slice and goal, exploration results, cross-concern blockers,
shared-file decisions, and final execution summary.

## Pipeline Order

1. Create `Documentation.md` first.
2. Create all 3 CSV files.
3. **Read phase** — Run `info-collection.csv` first with minimum 2 parallel
   helpers (default `explorer x2`). Close scope boundaries, blockers, and
   implementation targets here.
4. **Write phase** — Finalize `implementation.csv` rows only after
   info-collection completes. Execute as single-lane.
5. **Review phase** — Run `review.csv` after implementation completes with
   minimum 2 parallel reviewers (default `verification-worker` + domain
   reviewer).
6. Record final outcome in `Documentation.md`.

## CSV Schemas

### info-collection.csv (minimum 2 rows)

```csv
row_id,category,question,scope_boundary,assigned_agent_type,status,result_summary
ic-1,codebase,<exploration question>,<file/dir boundary>,explorer,pending,
ic-2,codebase,<exploration question>,<file/dir boundary>,explorer,pending,
```

### implementation.csv (1 row per target)

```csv
row_id,target_path,change_goal,assigned_agent_type,status,validation_command
impl-1,<primary file>,<exact change goal>,worker,pending,<validation cmd>
```

### review.csv (minimum 2 rows)

```csv
row_id,target_row_id,review_focus,assigned_agent_type,severity_gate,status,result_summary
rev-1,impl-1,<review focus>,verification-worker,advisory,pending,
rev-2,impl-1,<review focus>,explorer,advisory,pending,
```

## Hard Rules

- Read and review phases are always parallel with minimum 2 helpers.
- Write phase runs as single-lane.
- `implementation.csv` must exist even before implementation rows are finalized.
- Finalize implementation rows only after `info-collection.csv` closes.
- Auto-fix is allowed only for `critical` or `blocker` findings that have a
  row-local validation command and a small diff boundary.

## STATUS.md Ownership

This pipeline updates only these STATUS.md sections:

- `# Decisions made during implementation`
- `# Verification results`
- `# Known issues / residual risk`

Leave `# Current slice`, `# Done`, and `# Next slice` to `implement-task`.
