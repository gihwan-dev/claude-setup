# Parallel Workflow Runtime: SLICE-1

## Active slice

- `SLICE-1`
- Goal: API endpoint stubs via parallel runtime

## Locked routing contract

- Routing mode: `homogeneous`
- Assigned agent type: `codex-row-worker`
- Shard basis: endpoint file

## Cross-row blockers

- Shared-file exports are not row-local and must stay single-lane.

## Shared-file decisions

- `change_group_id=exports` owns shared export wiring.

## Final summary

- Runtime artifacts were created under this directory.
- Shared-file work was preserved as a single-lane fallback.
