---
name: multi-review
description: >
  Multi-agent code review for the current diff or a user-specified target.
  Use when the user asks to review code, requests a code review, says "review
  this", "check my changes", "multi-review", or "/multi-review". Runs 3 baseline
  reviewers in parallel, then adds conditional reviewers for frontend, architecture,
  or type contract changes. Do not use for single-file quick checks, linting, or
  when the user wants a quick opinion rather than a structured review.
context: fork
allowed-tools: Bash, Read, Grep, Glob, Agent
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
- Keep reviewer fan-out aligned with `${SKILL_DIR}/references/reviewer-matrix.md`.
- The default review target is the current worktree diff vs `HEAD`.
- If the user specifies a path, commit, or range, that target takes precedence.
- Synthesize the result as findings first and summary second.

## Workflow

1. Read `${SKILL_DIR}/references/reviewer-matrix.md` and lock the review target.
2. Always run the baseline reviewers in parallel, then add conditional reviewers based on the diff shape.
3. After reviewer fan-out, do only `wait` and result collection until results return. Pause additional file reads and searches in the main agent.
4. Order reviewer findings by severity and attach file or line evidence when possible.
5. Present findings first, then add only a short summary and residual risk if needed.

## Required References

- reviewer fan-out matrix, target precedence, synthesis contract: `${SKILL_DIR}/references/reviewer-matrix.md`

## Validation

- Confirm the 3 baseline reviewers are always included.
- Confirm the main agent does not continue file reads or searches between reviewer fan-out and result collection.
- Confirm `react-state-reviewer` is added for frontend diffs.
- Confirm `architecture-reviewer` or `type-specialist` is added when public or shared contract risk exists.
- Confirm the output stays findings first and summary second.
