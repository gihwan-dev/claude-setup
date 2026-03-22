---
name: multi-review
description: >
  Explicit multi-agent review entry for the current diff or a user-specified
  target.
---

# Multi Review

This is the explicit multi-agent review entry point, invoked after implementation work.
Always run the 3 baseline reviewers in parallel, then add extra reviewers only when the conditions justify it.

## Trigger

- `/multi-review`
- `$multi-review`
- `multi-review`

## Hard Rules

- Default to read-only review. Do not modify code.
- If multi-agent reviewer fan-out is unavailable in the runtime, report blocked instead of collapsing to a single review.
- Before reviewer results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After reviewer fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- Keep reviewer fan-out aligned with `${SKILL_DIR}/references/reviewer-matrix.md` and the workflow helper rules.
- The default review target is the current worktree diff vs `HEAD`.
- If the user specifies a path, commit, or range, that target takes precedence.
- Use `scripts/workflow_contract.py` to classify touched files before reviewer fan-out and derive `review_mode`, `hotspot_paths`, and maintainability metadata.
- Synthesize the result as findings first and summary second.

## Workflow

1. Read `${SKILL_DIR}/references/reviewer-matrix.md` and lock the review target.
2. Use the hotspot classifier in `scripts/workflow_contract.py` to decide whether review stays `diff-only` or upgrades to `diff+full-file-hotspots`.
3. Always run the baseline reviewers in parallel, then add conditional reviewers based on the diff shape.
4. If `hotspot_paths` is non-empty, keep the reviewer set unchanged but expand only `structure-reviewer` to `review_mode = diff+full-file-hotspots`; other reviewers stay diff-only.
5. Keep maintainability output separate from correctness, state, and test gap findings so it does not disappear into the summary.
6. After reviewer fan-out, do only `wait` and result collection until results return. Pause additional file reads and searches in the main agent.
7. Order reviewer findings by severity and attach file or line evidence when possible.
8. Present findings first, then add only a short summary and residual risk if needed.

## Required References

- reviewer fan-out matrix, target precedence, synthesis contract: `${SKILL_DIR}/references/reviewer-matrix.md`

## Validation

- Confirm the 3 baseline reviewers are always included.
- Confirm the main agent does not continue file reads or searches between reviewer fan-out and result collection.
- Confirm hotspot-aware runs upgrade only `structure-reviewer` to `diff+full-file-hotspots` and pass `hotspot_paths` when maintainability review is needed.
- Confirm `react-state-reviewer` is added for frontend diffs.
- Confirm `architecture-reviewer` or `type-specialist` is added when public or shared contract risk exists.
- Confirm the output stays findings first and summary second, with `maintainability` surfaced separately from `correctness`, `state`, and `test gap`.
