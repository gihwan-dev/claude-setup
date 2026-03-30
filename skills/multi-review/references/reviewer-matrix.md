# Multi Review Matrix

## Target Precedence

1. user-specified path
2. user-specified commit or range
3. current worktree diff vs `HEAD`

## Baseline Reviewers

Always run these 3 in parallel.

- `structure-reviewer`
- `code-quality-reviewer`
- `test-engineer`

## Conditional Reviewers

| Condition | Add reviewer |
|-----------|--------------|
| public surface changed / module boundary risk | `architecture-reviewer` |
| shared/public type changed / generics risk | `type-specialist` |
| React/TSX/frontend slice | `react-state-reviewer` |
| visual regression / browser repro needed | `browser-explorer` |

## Hotspot Full-File Pass

- Use `review_hotspots.py` output as the sole source of `review_mode`, `hotspot_paths`, `overflow_hotspot_paths`, and `maintainability_reasons`.
- If no hotspots: `review_mode = diff-only` for all reviewers.
- If hotspots: expand only `structure-reviewer` to `diff+full-file-hotspots` with `hotspot_paths`. Other reviewers stay diff-only.
- `hotspot_paths` is capped to top 3 by severity. Surface overflow in `maintainability_reasons`.

## Reviewer Return Contract

Each reviewer returns this shape. If unable, report `blocked` with a reason.

- `findings` — tagged items (`correctness`, `state`, `test gap`, or `maintainability`) with file/line evidence.
- `summary` — 1 short paragraph of key observations.
- `confidence` — `high`, `medium`, or `low`.

Compared to multi-work's Helper Return Contract: `evidence` is inlined into `findings` items. `target_paths` and `recommended_next_step` are omitted because review does not drive execution and the diff target is already known to the main agent.

## Timeout and Partial-Result Policy

- Treat a reviewer that does not return in reasonable time as stale; synthesize from the rest.
- A single stale, failed, or aborted reviewer must not block the fan-out.
- Record the absent reviewer and its expected contribution in a dedicated **Absent Reviewers** section of the synthesis output.
- If 2 of 3 baseline reviewers are absent, report the review as incomplete.

## Escalation Response Matrix

| Reviewer Signal | Main Thread Action |
|---|---|
| confidence: high | Include findings directly |
| confidence: medium | Include findings, note reduced confidence |
| confidence: low | Include findings with caveat; suggest follow-up. `split-replan` does not apply because review is read-only — mark as low-confidence and defer action to the user. |
| reviewer reports `blocked` | Record the gap; if baseline, mark review as partial |
| runtime fan-out unavailable | Stop and report blocked (do not proceed with partial dispatch) |
| conflicting findings | Surface the conflict and let the user judge (see Conflict Resolution) |

## Conflict Resolution

- When reviewers return conflicting findings, prefer the one with higher confidence.
- At equal confidence, surface the conflict and request user judgment.
- When structural judgment (`structure-reviewer`) conflicts with domain judgment (`type-specialist`, `react-state-reviewer`), default to structural judgment but record the rationale.

## Output Contract

- Findings first, summary second.
- Order findings by severity. Attach file or line evidence.
- Tag each finding as `correctness`, `state`, `test gap`, or `maintainability`.
- Keep `maintainability` separate from other tags so it is not buried.
- When hotspot files were reviewed, emit a `maintainability_verdict` line before the summary.
- List dropped (budget) or absent (timeout/abort) reviewers in an **Absent Reviewers** section with reasons.
- Add open questions and residual risk after the findings.
- This skill performs review only and does not make edits.
