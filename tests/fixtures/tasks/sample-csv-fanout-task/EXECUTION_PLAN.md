# Execution slices

## SLICE-1: API endpoint stubs via CSV fan-out

- Orchestration: manager lane + csv-fanout workers
- Preflight helpers: explorer + structure-reviewer
- Implementation owner: codex-row-worker
- Integration owner: codex-row-worker
- Validation owner: verification-worker
- Allowed main-thread actions: bundle-doc synthesis + helper-result synthesis + handoff/STATUS/commit coordination
- Change boundary: Each row worker creates files under its `target_path`.
- Expected files: 1 per CSV row (up to 4 concurrent).
- Focused validation plan: Row output schema check + shared file integrity.
- Stop / Replan trigger: >50% row failure rate.
- Fan-out spec: `work-items/SLICE-1-items.csv`, concurrency 4, staged batch mode.
- Split decision: N/A — each row is independently scoped.

# Verification

- Row output CSV matches `schemas/row-result.schema.json`.
- Integrator shared-file merge has no conflicts.
- `python3 -m unittest discover -s tests -p 'test_*.py'`

# Stop / Replan conditions

- Row failure rate exceeds 50%.
- Shared file merge conflict detected.
- New cross-row dependency discovered.
