---
name: fanout
description: >
  Compatibility entrypoint for multi-agent orchestration. Fanout no longer uses
  CSV pipelines. Instead, it routes to plan/build workflows that use sub-agents
  for scoped discovery, isolated implementation slices, and independent review.
  Invoke with "$fanout" when you want helper-driven execution.
allowed-tools: Read, Grep, Glob, Write, Agent
---

# Fanout (Compatibility Mode)

`fanout` is now a routing skill, not a standalone CSV pipeline.

Use it when the user asks for multi-agent execution. Route the task into:

- `plan` for helper-driven discovery + milestone/orchestration design
- `build` for approved milestone execution with worker/reviewer helpers

## Trigger

- `$fanout`
- `/fanout`

## Why This Changed

Parallelism is useful, but speed is not the main reason to use sub-agents.

Primary reasons:

1. **Context isolation**: broad tasks can make one agent read too much,
   pulling irrelevant details into active context.
2. **Independent progress**: long-running tasks should advance in focused,
   bounded slices without forcing one giant context window.
3. **Review quality**: an implementation agent is often not critical enough of
   its own work; separate reviewers reduce self-confirmation bias.

## Routing Rules

1. No `work-items.csv`, no CSV schema, no CSV-based execution state.
2. If no `tasks/<slug>/BRIEF.md` exists, run the `plan` workflow first.
3. If an approved brief exists, run the `build` workflow.
4. For ambiguous scope, dispatch **scoped read helpers** before coding.
5. For implementation, use **bounded worker slices** with explicit scope.
6. For validation, use **independent reviewer helpers** that did not author
   the code being reviewed.
7. Before long-running execution, present helper plan and wait for user
   approval.

## Expected Handoff Output

When routing from `fanout`, provide a short handoff summary:

```text
Fanout routed to <plan|build>

Why helpers:
- <context-isolation reason>
- <review-quality reason>

Next:
- <what happens now>
```
