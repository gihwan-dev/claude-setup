# Phase Report 03: Variant Generator

## Summary

Implemented the Phase 3 Variant Generator CLI at `scripts/hyperagent/generate_variant.py`.

The CLI reads Phase 2 `score-report.json`, consumes its top-level `improvements` list, loads the matching SSOT profile from `agent-registry/<agent-id>/instructions.md` or `skills/<skill>/SKILL.md`, and writes rule-based prompt variants under `scripts/hyperagent/variants/<entity-id>/<variant-id>/`.

The initial generation mode does not call an LLM. It appends the improvement suggestion as a Markdown comment patch at the end of the copied profile and writes `meta.json` with source path, score, evidence, change reason, and staged status. The `--llm` flag is accepted as a future interface but still uses rule-based generation in this phase.

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `scripts/hyperagent/generate_variant.py` | Created | Adds the Variant Generator CLI, score-report parsing, target filtering, source profile loading, rule-based patch generation, variant writing, `meta.json`, `--dry-run`, and JSON/text output. |
| `scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/instructions.md` | Generated | Rule-based variant for `agent:architecture-reviewer`. |
| `scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/meta.json` | Generated | Variant metadata for `agent:architecture-reviewer`. |
| `scripts/hyperagent/variants/code-quality-reviewer/v-20260413-061715-02/instructions.md` | Generated | Rule-based variant for `agent:code-quality-reviewer`. |
| `scripts/hyperagent/variants/code-quality-reviewer/v-20260413-061715-02/meta.json` | Generated | Variant metadata for `agent:code-quality-reviewer`. |
| `scripts/hyperagent/variants/design-evaluator/v-20260413-061715-03/instructions.md` | Generated | Rule-based variant for `agent:design-evaluator`. |
| `scripts/hyperagent/variants/design-evaluator/v-20260413-061715-03/meta.json` | Generated | Variant metadata for `agent:design-evaluator`. |
| `tasks/hyperagent-integration/PHASE_REPORT_03.md` | Created | Records Phase 3 implementation notes, changed files, and verification results. |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Use only the top-level `improvements` list as input. | The task defines Phase 2 output as `entities`, `improvements`, and `baseline_status`; this keeps the generator on the documented Phase 2 contract. |
| Keep the default output directory at `scripts/hyperagent/variants`. | Matches the requested storage path for this phase, even though API-CONTRACT also discusses later `variants/staging` layouts. |
| Generate Markdown comment patches. | The current mutable profiles are Markdown files (`instructions.md`, `SKILL.md`), and the task asks for `original + improvement patch` without mutating SSOT originals. |
| Preserve API-CONTRACT aliases where harmless. | `--scores` is accepted as an alias for `--input`; `--max-variants`, `--strategy`, `--output-dir`, `--registry`, and `--skills` are included for the interface shape. |
| Treat `--llm` as an accepted placeholder. | Phase 3 explicitly excludes LLM API calls while asking to prepare the future interface. The command warns and continues with rule-based generation. |

## Verification Results

| Command | Result | Notes |
|---------|--------|-------|
| `python3 -m py_compile scripts/hyperagent/generate_variant.py` | PASS | Syntax check passed. The generated `__pycache__` file was removed afterward. |
| `python3 scripts/hyperagent/analyze_sessions.py --date-range 2026-04-12 2026-04-13 --json \| python3 scripts/hyperagent/score.py --json > /tmp/score-report.json` | PASS | Required Phase 1 + Phase 2 pipeline produced `/tmp/score-report.json`. It emitted the known baseline write warning because the sandbox cannot write `/Users/choegihwan/.claude/hyperagent/baseline.json`. |
| `python3 scripts/hyperagent/generate_variant.py --input /tmp/score-report.json --json \| python3 -m json.tool` | PASS | Generated 3 variants and emitted valid JSON. |
| `find scripts/hyperagent/variants -maxdepth 4 -type f \| sort` | PASS | Confirmed each generated variant directory contains the copied profile file and `meta.json`. |
| `tail -n 18 scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/instructions.md` | PASS | Confirmed the variant content is original profile content plus a trailing HyperAgent improvement patch comment. |
| `python3 -m json.tool scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/meta.json` | PASS | Confirmed `meta.json` is valid JSON and contains original path, source score, evidence sessions, suggestion reason, and staged status. |
| `python3 scripts/hyperagent/generate_variant.py --input /tmp/score-report.json --target architecture-reviewer --dry-run --json \| python3 -m json.tool` | PASS | Target filtering worked and emitted a single planned variant. |
| File count check before/after dry-run | PASS | `scripts/hyperagent/variants` file count remained `6 -> 6`; dry-run created no files. |

## Changed Files

- `scripts/hyperagent/generate_variant.py`
- `scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/instructions.md`
- `scripts/hyperagent/variants/architecture-reviewer/v-20260413-061715/meta.json`
- `scripts/hyperagent/variants/code-quality-reviewer/v-20260413-061715-02/instructions.md`
- `scripts/hyperagent/variants/code-quality-reviewer/v-20260413-061715-02/meta.json`
- `scripts/hyperagent/variants/design-evaluator/v-20260413-061715-03/instructions.md`
- `scripts/hyperagent/variants/design-evaluator/v-20260413-061715-03/meta.json`
- `tasks/hyperagent-integration/PHASE_REPORT_03.md`
