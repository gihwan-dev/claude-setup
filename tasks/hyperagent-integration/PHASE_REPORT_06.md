# Phase 06 Report: Evolution Pipeline CLI

## Summary

Implemented `scripts/hyperagent/evolve.py` as the Meta-Loop Trigger entrypoint for the full HyperAgent pipeline:

- `analyze_sessions.py` -> `score.py` -> `generate_variant.py` -> `archive.py add` -> `apply.py`
- Pipes JSON output from each stage into the next stage via stdin/stdout.
- Records per-step `status`, command, return code, stderr, and output summaries in `pipeline_steps`.
- Defaults `--date-range` to the previous local day when omitted.
- Supports `--dry-run` by running analysis/scoring/generation safely and simulating archive/apply without writing variants, archive records, tags, or SSOT changes.
- Supports `--json` structured output and includes a crontab example in `--help`.
- Uses a temporary baseline path for `score.py` during dry-run to avoid persistent baseline writes.

Added `scripts/hyperagent/com.hyperagent.evolve.plist` as the macOS launchd schedule file for daily 22:00 execution. The plist is a file-only configuration artifact; it was not loaded into launchd.

## Changed Files

- `scripts/hyperagent/evolve.py`
- `scripts/hyperagent/com.hyperagent.evolve.plist`
- `tasks/hyperagent-integration/PHASE_REPORT_06.md`

## Behavior

- Default manual run:
  - `python3 scripts/hyperagent/evolve.py --json`
  - Runs the full pipeline for yesterday's sessions.
- Dry-run:
  - `python3 scripts/hyperagent/evolve.py --dry-run --json`
  - Runs `analyze`, `score`, and `generate --dry-run`.
  - Simulates `archive` and `apply` outputs with `simulated: true`.
- Date range:
  - `python3 scripts/hyperagent/evolve.py --date-range 2026-04-12 2026-04-12 --dry-run --json`
- Daily launchd schedule:
  - Label: `com.hyperagent.evolve`
  - Program: `/usr/bin/python3 /Users/choegihwan/Documents/Projects/claude-setup/scripts/hyperagent/evolve.py --json`
  - Working directory: `/Users/choegihwan/Documents/Projects/claude-setup`
  - Time: every day at 22:00

## Verification

- Passed: `python3 scripts/hyperagent/evolve.py --dry-run --json | python3 -m json.tool`
- Passed: `python3 scripts/hyperagent/evolve.py --dry-run --json | python3 -c 'import json, sys; payload=json.load(sys.stdin); steps=payload.get("pipeline_steps"); assert isinstance(steps, list), "pipeline_steps missing or not a list"; missing=[step.get("name", "<unknown>") for step in steps if "status" not in step]; assert not missing, "steps missing status: " + ", ".join(missing); print("pipeline_steps:", [step["name"] for step in steps]); print("statuses:", {step["name"]: step["status"] for step in steps})'`
  - Result: `pipeline_steps: ['analyze', 'score', 'generate', 'archive', 'apply']`
  - Result: `statuses: {'analyze': 'success', 'score': 'success', 'generate': 'success', 'archive': 'success', 'apply': 'success'}`
- Passed: `plutil -lint scripts/hyperagent/com.hyperagent.evolve.plist`
  - Result: `scripts/hyperagent/com.hyperagent.evolve.plist: OK`
- Passed: `python3 scripts/hyperagent/evolve.py --help | rg -n "Crontab example|0 22|crontab|evolve.py --json"`
  - Result includes the crontab example at daily 22:00.
- Passed: `python3 -m py_compile scripts/hyperagent/evolve.py`

No Phase 1-5 CLI files were modified. No crontab or launchd registration command was run.
