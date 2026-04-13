# Phase 05 Report: Improvement Applier CLI

## Summary

- Added `scripts/hyperagent/apply.py` to plan and apply HyperAgent variants into the SSOT.
- Added `scripts/hyperagent/improvement-log.jsonl` as the append-only application log.
- Implemented dry-run JSON output, archive selection, Tier handling, Tier 3 pending proposals, pipeline execution hooks, `[hyperagent]` commits, and rollback via `git revert`.

## Changed Files

- `scripts/hyperagent/apply.py`
- `scripts/hyperagent/improvement-log.jsonl`
- `tasks/hyperagent-integration/PHASE_REPORT_05.md`

## Behavior

- `--variant-dir <path>` loads a variant directory directly.
- `--from-archive --entity <agent-id>` calls `scripts/hyperagent/archive.py select --entity <agent-id> --json`.
- Tier 1 applies existing agent profile updates.
- Tier 2 applies existing skill prompt updates and records a 3-session observation window.
- Tier 3 requires `--approve`; without approval it writes a pending proposal under `scripts/hyperagent/proposals/`.
- Non-dry-run application copies the variant payload to SSOT, creates a `[hyperagent]` git commit, runs `scripts/sync_agents.py`, runs `scripts/install_assets.py --link`, and appends `scripts/hyperagent/improvement-log.jsonl`.
- `--rollback <commit-hash>` verifies the commit subject starts with `[hyperagent]`, runs `git revert --no-edit`, and appends a rollback event.

## Verification

- Passed: `python3 -m py_compile scripts/hyperagent/apply.py`
- Passed: `python3 scripts/hyperagent/apply.py --variant-dir scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715 --dry-run --json | python3 -m json.tool`
- Passed: dry-run output includes `tier`, `action`, and `target_path`.
- Passed: `git status --short agent-registry` was empty before and after dry-run.
- Passed: `python3 scripts/hyperagent/apply.py --from-archive --entity architecture-reviewer --dry-run --json | python3 -m json.tool`
