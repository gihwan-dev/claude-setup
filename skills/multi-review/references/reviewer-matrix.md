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

## Synthesis Contract

- Before reviewer results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After reviewer fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Results are findings first and summary second.
- Order findings by severity.
- Attach file or line evidence when possible.
- Add open questions and residual risk briefly after the findings.
- This skill performs review only and does not make edits.
