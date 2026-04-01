---
name: plan
description: >
  Read-only task planning skill. Invoke when the user writes "plan" or "$plan".
  Explores the codebase, clarifies requirements with the user, and produces a
  single BRIEF.md under tasks/<slug>/. Covers both product scope (what/why) and
  implementation design (how/milestones). Do not use for code changes or quick
  fixes that need no planning.
allowed-tools: Read, Grep, Glob, Write, Agent
---

# Plan

Turn a user request into a clear, actionable `BRIEF.md`. This single document
replaces all prior bundle artifacts (task.yaml, EXECUTION_PLAN.md, etc.).

## Hard Rules

1. No code edits. Read-only exploration only.
2. Produce exactly one file: `tasks/<slug>/BRIEF.md`.
3. If a `BRIEF.md` already exists for this task, read and update it — do not
   create a new one.
4. If `docs/ai/ENGINEERING_RULES.md` exists in the repo, reference it for
   implementation decisions — do not copy or regenerate.
5. Each milestone must be specific, independently verifiable, and ordered.
6. Ask the user when ambiguous — batch up to 3 questions at a time.
7. Sub-agents (Explorer, web-researcher, etc.) may be used for read-only
   exploration.
8. Do not prescribe agent orchestration. The `build` skill decides helpers at
   runtime.

## BRIEF.md Format

```markdown
# <Task Title>

## Goal
What and why (1-3 sentences).

## Scope
In scope, out of scope, do not touch.

## Approach
Technical decisions, libraries, architecture — free-form, as much as needed.

## Milestones
Ordered list. Each milestone:
- **what**: What changes
- **verify**: How to confirm completion
- **budget**: Estimated files / LOC (optional)

## Status
- current: (milestone name or "not started")
- done: (list)
- blocked: (if any)

## Log
(append-only: date + decisions / outcomes / changes)
```

## Workflow

1. Check `tasks/` for an existing `BRIEF.md` matching the request.
2. Explore the codebase — use sub-agents when the scope is broad.
3. Ask clarifying questions if requirements are ambiguous.
4. Write or update `BRIEF.md` with Goal, Scope, Approach, Milestones.
5. Present to the user for confirmation.

## Session Resumption

Read `tasks/<slug>/BRIEF.md` → check Status → continue from where it left off.
No continuity gate or signal comparison needed.
