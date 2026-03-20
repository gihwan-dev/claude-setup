# Clean Code Inspector Scoring Model v2.1

## 1) Purpose

This document defines the scoring rules for clean-code-inspector v2.1.
The core principle is to layer an **evidence-based qualitative overlay** on top of **AST/static-analysis quantitative measurement**.

## 2) Final Score Formula

- Quantitative score (0-100): `Q`
- Qualitative score (0-100): `S`
- Final score (0-100): `F`

`F = Q * 0.85 + S * 0.15`

When all qualitative data is `N/A`:
- `F = Q`
- Record the reason for `N/A` in `unavailableMetrics`

## 3) Quantitative Axes and Weights

The quantitative model fixes these four axes:

1. Complexity (35)
2. Type Safety (30)
3. Test Reliability (20)
4. Change Risk (15)

If there is not enough data for an axis, mark that axis as `N/A`.
Do not renormalize the weights per axis.

## 4) Qualitative Overlay Scope

- Apply qualitative evaluation only to files in the top 20% of quantitative hotspots
- Always include at least one file, even when the total file count is small

## 5) Qualitative Criteria and Score Conversion

The qualitative overlay fixes these five criteria:

1. Intent Clarity
2. Local Reasoning
3. Failure Semantics
4. Boundary Discipline
5. Test Oracle Quality

Each criterion is scored from `0~4`. If the average criterion score is `avgC`:

`S = avgC * 25`

## 6) Handling Insufficient Evidence

Each criterion needs at least two code evidence points (file + line) to count.
- Fewer than two evidence points: criterion score is `N/A`
- Exclude `N/A` criteria from the average

## 7) No Qualitative-Only Fail

If the quantitative score is not a fail, the qualitative overlay must not drag the final result into fail.
- Fail threshold: `F < 50` (grade F)
- If `Q >= 50` and `F < 50`, clamp `F` to 50 and leave a log entry

## 8) Critical Flag Rules

Emit forced warnings for the following items regardless of grade:

- `boundary_discipline_violation`
- `missing_failure_semantics`

Always record Critical Flags in `criticalFlags[]` and print them in the `Critical Flags` section of `clean-code-inspect-result.md`.

## 9) Grade Bands

- A: 90-100
- B: 80-89.99
- C: 70-79.99
- D: 60-69.99
- E: 50-59.99
- F: 0-49.99

## 10) Output Schema Requirements

### `quantitative-metrics.json`

- `schemaVersion`, `generatedAt`, `profile`, `analysisMode`
- `files[]`: `{ path, metrics, hotspotScore }`
- Required keys inside `files[].metrics`:
  - `cyclomatic`, `cognitive`, `halsteadVolume`, `maintainabilityIndex`
  - `locLogical`, `locPhysical`, `importCount`, `stateCount`
  - `anyCount`, `assertionCount`, `tsIgnoreCount`
  - `lineCoverage`, `branchCoverage`, `mutationScore`
  - `churnLines`, `churnTouches`
  - `fanIn`, `fanOut`, `instability`, `circular`
- `axes`: `complexity`, `typeSafety`, `testReliability`, `changeRisk`
- `summary`: `quantitativeScore`, `quantitativeGrade`
- `unavailableMetrics[]`

### `clean-code-inspect-result.json`

- `qualitativeOverlay.criteria[]`
- `qualitativeOverlay.score`
- `qualitativeOverlay.evidence[]`
- `criticalFlags[]`
