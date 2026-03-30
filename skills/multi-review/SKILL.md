---
name: multi-review
description: >
  Multi-agent code review for the current diff or a user-specified target.
  Use when the user asks to review code, requests a code review, says "review
  this", "check my changes", "multi-review", or "/multi-review". Runs 3 baseline
  reviewers in parallel, then adds conditional reviewers for frontend, architecture,
  or type contract changes. Typically invoked after implementation work. Do not use
  for single-file quick checks, linting, or when the user wants a quick opinion
  rather than a structured review.
context: fork
allowed-tools: Bash, Read, Grep, Glob, Agent
---

# Multi Review

## Trigger

- `/multi-review`
- `$multi-review`
- `multi-review`

## Hard Rules

- Read-only review. Do not modify code.
- If runtime fan-out is unavailable, report blocked instead of collapsing to a single review.
- After dispatching reviewers, do only `wait` and result collection. Do not read files, run searches, or do parallel side work until all results return.

## Dispatch Prompt Contract

Each reviewer's dispatch prompt contains exactly these items and nothing else:

1. **Review target** — the diff range, commit, or file paths to review.
2. **Review mode** — `diff-only` or `diff+full-file-hotspots` with `hotspot_paths` (for `structure-reviewer` only).
3. **Return shape** — the Reviewer Return Contract from `reviewer-matrix.md` (findings, summary, confidence).

Do not include references to this SKILL.md, `reviewer-matrix.md`, orchestration rules, budget, fan-out, wait discipline, or any other file in the skill directory. Reviewers have their own profile via `developer_instructions`; the dispatch prompt adds only the target, mode, and expected output shape.

## Workflow

1. Read `${SKILL_DIR}/references/reviewer-matrix.md` and lock the review target.
2. Collect `git diff --numstat` for the chosen target, then pipe it into `python3 "${SKILL_DIR}/../_shared/scripts/review_hotspots.py" --input-format numstat --policy-root "$PWD"`.
3. Select reviewers per the baseline and conditional tables. Check `max_helpers_per_fanout` from `policy/workflow.toml` (default 4); if the total exceeds the budget, drop conditional reviewers from the bottom of the table until it fits.
4. Expand `structure-reviewer` to `diff+full-file-hotspots` mode when `hotspot_paths` is non-empty; other reviewers stay diff-only.
5. Compose each reviewer's dispatch prompt per the Dispatch Prompt Contract above.
6. Dispatch reviewers in parallel.
7. Wait for results. Follow the timeout, partial-result, escalation, and conflict resolution policies in `reviewer-matrix.md`.
8. Synthesize per the output contract in `reviewer-matrix.md`.

## Required References

- Reviewer selection, return contract, resilience policies, output contract: `${SKILL_DIR}/references/reviewer-matrix.md`
- Fan-out budget: `policy/workflow.toml` `[orchestration_budget]`
