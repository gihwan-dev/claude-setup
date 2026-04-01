# Execution slices

## SLICE-1: API endpoint stubs via parallel runtime

- Change boundary: API endpoint stub files plus one shared-file change-group lane.
- Expected files: 4 row-local files, with shared-file work collapsed to single-lane integration.
- Orchestration: manager lane + `implement-task` runtime.
- Preflight helpers: `explorer` + `structure-reviewer`
- Execution skill: `implement-task`
- Implementation owner: `implement-task`
- Integration owner: `implement-task`
- Validation owner: `verification-worker`
- Allowed main-thread actions: bundle-doc synthesis + handoff + STATUS/commit coordination
- Focused validation plan: row-local validation commands are recorded in `review.csv`, then summarized for the manager lane.
- Stop / Replan trigger: blocked routing inputs, overlapping shared-file writes without a change group, or more than 50% failed runtime rows.
- Split decision: keep parallel rows only for row-local files; collapse shared-file work into a single lane.

# Verification

- `implement-task` creates `Documentation.md`, `info-collection.csv`,
  `implementation.csv`, and `review.csv` under `runs/SLICE-1/`.
- Shared-file rows are marked `parallelizable=false` or share the same
  `change_group_id`.
- `python3 -m unittest discover -s tests -p 'test_*.py'`

# Stop / Replan conditions

- Routing inputs are not locked, so `$multi-work` is required first.
- Shared-file ownership cannot be reduced to a single lane.
- Review findings require fixes outside row-local validation boundaries.
