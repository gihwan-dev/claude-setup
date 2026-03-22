# Multi Review Matrix

## Target Precedence

1. user-specified path
2. user-specified commit or range
3. current worktree diff vs `HEAD`

## Baseline Reviewers

Run these 3 reviewers in parallel every time.

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

- Before reviewer fan-out, classify touched files with `scripts/workflow_contract.py`.
- If no hotspots are selected, keep `review_mode = diff-only` for every reviewer.
- If hotspot files are selected, keep the baseline reviewers unchanged and expand only `structure-reviewer`.
- Pass `review_mode`, `review_mode = diff+full-file-hotspots`, and `hotspot_paths` to `structure-reviewer`.
- `hotspot_paths` is capped to the top 3 files by severity. If more files qualify, keep the cap and surface the overflow in maintainability reasons.
- Other reviewers continue reviewing the diff only.

## Synthesis Contract

- Before reviewer results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After reviewer fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Results are findings first and summary second.
- Order findings by severity.
- Attach file or line evidence when possible.
- Tag findings as `correctness`, `state`, `test gap`, or `maintainability`.
- When hotspot files were reviewed, emit a separate `maintainability_verdict` line before the short summary.
- Add open questions and residual risk briefly after the findings.
- This skill performs review only and does not make edits.
