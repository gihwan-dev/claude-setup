---
name: clean-code-inspector
description: >
  AST-based TS/JS code quality analysis combining quantitative metrics (85%) and qualitative rubric overlay (15%).
  Specialized TS/JS code quality inspection that combines AST/static-analysis metrics with an evidence-based
  qualitative overlay to generate `clean-code-inspect-result.json` and `.md`.
  Triggers: "code review", "quality inspection", "clean code", "inspection", "code analysis", etc.
---

# Clean Code Inspector v2.1 (AST-Based Quantitative Metrics + Qualitative Overlay)

## Core Principles

- **Generate quantitative metrics automatically**: Use AST/static-analysis tools to create `quantitative-metrics.json` instead of manual counting.
- **Qualitative scoring is an overlay**: Apply it only to the top 20% of quantitative hotspots.
- **Evidence is mandatory**: Mark a qualitative item as `N/A` unless it has at least two file+line evidence points.
- **Fixed weights**: The final score uses `quantitative 85% + qualitative 15%`.
- **No qualitative-only fail**: Do not fail a result when the quantitative score passes and only the qualitative score is low.

## Phase 1: Interpret Inputs and Collect Files

Map user arguments to the diff command using the table below.

| Input pattern | File listing command | Analysis mode |
|-----------|---------------|-----------|
| (none) | `git diff --name-only` | `working` |
| `staged`, `--cached` | `git diff --cached --name-only` | `staged` |
| Branch name (for example `main`, `develop`) | `git diff {branch}...HEAD --name-only` | `branch` + target=branch |
| Commit range `abc..def` | `git diff abc..def --name-only` | `range` + target=abc..def |
| Direct file path input | (use the input as-is) | `files` + target="a.ts,b.ts" |

Filtering rules:
- Include: `.ts`, `.tsx`, `.js`, `.jsx`
- Exclude: `node_modules/`, `.d.ts`, `*.config.ts`, `*.config.js`, `*.stories.tsx`, `dist/`, `build/`
- If the result count is 0: print `No analyzable changed files.` and exit
- If the result count exceeds 25: confirm whether the scope should be narrowed first

## Phase 2: Ensure the Toolchain and Collect Quantitative Metrics

### 2-1) Ensure the Toolchain

First, verify dependency availability with this command.

```bash
node "${SKILL_DIR}/scripts/ensure-toolchain.mjs" \
  --skill-dir "${SKILL_DIR}" \
  --auto-install true
```

Execution rules:
- If packages are missing, automatically try `pnpm --dir <skill_dir> install --frozen-lockfile` once
- If that fails, continue with `analysisMode=degraded`
- Record missing-tool reasons in `unavailableMetrics`

### 2-2) Generate Quantitative JSON

```bash
node "${SKILL_DIR}/scripts/collect-quantitative-metrics.mjs" \
  --project-root "{project_root}" \
  --mode "{working|staged|branch|range|files}" \
  --target "{target_if_needed}" \
  --window-days 90 \
  --profile "balanced" \
  --out ".clean-code-inspector/quantitative-metrics.json" \
  --out-unavailable ".clean-code-inspector/unavailable-metrics.json"
```

Collection rules:
- The default analysis scope is `changed files + import closure`
- Traverse the import closure with BFS, capped at 300 files by default
- If the cap is exceeded, truncate the scope and record that in `unavailableMetrics`

Outputs:
- `.clean-code-inspector/quantitative-metrics.json`
- `.clean-code-inspector/unavailable-metrics.json`

## Phase 3: Select the Top 20% Hotspots

Sort `files[].hotspotScore` from the quantitative JSON in descending order.
- Only the top `max(1, ceil(N * 0.2))` files become qualitative review targets

## Phase 4: Qualitative Overlay

Run `architecture-reviewer` only on hotspot files.

Reference documents:
- `references/qualitative-rubric.md`
- `references/scoring-model-v2.md`

Required rules:
- Evaluate only these five criteria: `Intent Clarity`, `Local Reasoning`, `Failure Semantics`, `Boundary Discipline`, `Test Oracle Quality`
- Use an anchored `0~4` rubric for each criterion
- If a criterion has fewer than two evidence points, mark it `N/A`
- Always record `Boundary Discipline` violations and missing `Failure Semantics` in `criticalFlags`

Outputs:
- `.clean-code-inspector/qualitative-overlay.json`

## Phase 5: Generate the Scorecard

```bash
node "${SKILL_DIR}/scripts/build-scorecard.mjs" \
  --quant ".clean-code-inspector/quantitative-metrics.json" \
  --qual ".clean-code-inspector/qualitative-overlay.json" \
  --out-json "clean-code-inspect-result.json" \
  --out-md "clean-code-inspect-result.md" \
  --profile "balanced"
```

Result rules:
- Final score = `quantitativeScore × 0.85 + qualitativeScore × 0.15`
- No qualitative-only fail
- Display `criticalFlags[]` as warnings regardless of grade

## Phase 6: Output a User Summary

The final summary must include:
- Number of analyzed files
- Quantitative score, qualitative score, and final score
- Number of hotspot files
- Critical Flags summary
- Saved path for `clean-code-inspect-result.md`

## Required Report Sections

`clean-code-inspect-result.md` must contain these sections:
1. `Qualitative Overlay Results`
2. `Quantitative-Qualitative Cross Signals`
3. `Critical Flags`
