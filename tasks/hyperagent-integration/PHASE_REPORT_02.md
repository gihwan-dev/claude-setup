# Phase Report 02: Performance Scorer

## Summary

Implemented the Phase 2 Performance Scorer CLI at `scripts/hyperagent/score.py`. The scorer reads the Phase 1 `analysis-report.json` from `--input` / `--report` or stdin, computes decay-weighted agent, skill, and orchestration scores, compares those scores to a baseline file, and emits ranked improvement candidates as JSON.

The output includes both API-CONTRACT compatible `scores` and the requested top-level `entities`, `improvements`, and `baseline_status` keys.

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `scripts/hyperagent/score.py` | Created | Adds the Performance Scorer CLI, scoring models, stdin support, baseline tracking, improvement ranking, complexity normalization, trend detection, and git-blame adoption metric hooks. |
| `tasks/hyperagent-integration/PHASE_REPORT_02.md` | Created | Records Phase 2 implementation notes, decisions, validation, and open issues. |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Support both `--input` and `--report`. | The task asks for `--input`, while API-CONTRACT names `--report`; both map to the same analyzer JSON input. |
| Preserve `scores` while adding `entities`. | API-CONTRACT downstream phases can consume `scores`; the Phase 2 verification requires `entities`. Both point to the same scored objects. |
| Score from session-level attribution. | Phase 1 emits entity activity per session, not message-span boundaries. The scorer therefore computes per-session samples for each active entity and uses weighted aggregation. |
| Apply time decay and session length weighting. | Recent sessions use half-life 7 days; longer sessions get `ln(turn_count + 1)` weight, matching ANALYTICS.md aggregation guidance. |
| Normalize negative signals by complexity. | Negative signals are multiplied by Phase 1 `negative_signal_weight_factor`, so complex tasks are penalized less sharply than simple tasks. |
| Establish baselines only with at least 5 entity sessions. | Follows ANALYTICS.md minimum-session rule and records lower-volume entities in `baseline_status.entities_pending`. |
| Keep commit adoption as an auxiliary metric. | The scorer implements git-blame based calculation when touched files are present in analyzer reports. Current Phase 1 JSON does not emit `files_touched`, so most entities report this metric as unavailable with an explicit reason. |
| Generate deterministic improvement text. | The CLI needs to run locally and repeatably. It turns weak score dimensions into targeted suggestions and leaves variant generation to later phases. |

## Impact on Future Phases

- Phase 3 can consume `improvements` directly as the ranked list of candidates for variant generation.
- `baseline_status` exposes which entities have enough sessions for stable comparison, avoiding premature improvement triggers.
- The output keeps `commit_adoption_rate` in each entity object, so a future analyzer that emits touched files can activate the git-blame metric without changing the score report schema.
- Orchestration now has its own scored entity, allowing later policy evolution to target routing and fan-out behavior separately from individual agents or skills.

## Open Issues

- The default baseline path is `~/.claude/hyperagent/baseline.json`, but this Codex sandbox cannot write to `/Users/choegihwan/.claude`. The required default-path command still produced valid JSON with `baseline_status.state: "write_failed"`. Baseline creation was verified with a writable `/tmp` path.
- Phase 1 does not include touched file lists in `signals.by_session`, so git-blame commit adoption is implemented but usually unavailable for current analyzer output.
- Entity attribution remains session-level until the analyzer emits finer-grained entity spans.

## Verification Results

| Command | Result | Notes |
|---------|--------|-------|
| `python3 -m py_compile scripts/hyperagent/score.py` | PASS | Syntax check passed. |
| `python3 scripts/hyperagent/analyze_sessions.py --date-range 2026-04-12 2026-04-13 --json \| python3 scripts/hyperagent/score.py --json \| python3 -m json.tool` | PASS | Required stdin pipeline emitted valid JSON. The command also reported `baseline_status.state: "write_failed"` because the sandbox cannot create `/Users/choegihwan/.claude/hyperagent/baseline.json`. |
| Required key check for `entities`, `improvements`, `baseline_status` on the required pipeline output | PASS | All three top-level keys were present. |
| `python3 scripts/hyperagent/score.py --input /tmp/hyperagent-analysis-report.json --json \| python3 -m json.tool` | PASS | Required `--input <analysis-report.json> --json` mode emitted valid JSON. It reported `baseline_status.state: "write_failed"` for the default baseline path under sandbox permissions. |
| `python3 scripts/hyperagent/analyze_sessions.py --date-range 2026-04-12 2026-04-13 --json > /tmp/hyperagent-analysis-report.json && python3 scripts/hyperagent/score.py --input /tmp/hyperagent-analysis-report.json --baseline /tmp/hyperagent-baseline-input.json --json \| python3 -m json.tool` | PASS | `--input` file mode emitted valid JSON. |
| `python3 scripts/hyperagent/score.py --input /tmp/hyperagent-analysis-report.json --baseline /tmp/hyperagent-baseline-input.json --json` key check | PASS | Confirmed `entities`, `improvements`, and `baseline_status` exist. |
| `python3 scripts/hyperagent/score.py --input /tmp/hyperagent-analysis-report.json --baseline /tmp/hyperagent-baseline-create.json --json \| python3 -m json.tool` | PASS | Writable baseline path was automatically created. |
| `python3 scripts/hyperagent/analyze_sessions.py --date-range 1900-01-01 1900-01-02 --json \| python3 scripts/hyperagent/score.py --baseline /tmp/hyperagent-empty-baseline.json --json \| python3 -m json.tool` | PASS | 0-session analyzer output returned valid JSON with empty scored entities. |
| Synthetic no-entity report through `score.py --json` | PASS | Report with no agent or skill invocations returned empty agents, skills, and improvements with exit 0. |

## Changed Files

- `scripts/hyperagent/score.py`
- `tasks/hyperagent-integration/PHASE_REPORT_02.md`
