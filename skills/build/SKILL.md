---
name: build
description: >
  Execute the next milestone from an approved BRIEF.md. Invoke when the user
  writes "build" or "$build". Reads the brief, picks the next milestone,
  implements code changes, runs verification, and updates Status/Log. Do not
  use without an existing BRIEF.md — run plan first.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Build

Execute milestones from `tasks/<slug>/BRIEF.md` one at a time.

## Hard Rules

1. If no `BRIEF.md` exists or Milestones is empty, stop and suggest `$plan`.
2. Execute one milestone per invocation. If the user says "keep going" or
   "until done", continue through remaining milestones.
3. Before starting a milestone, read all relevant code. Use sub-agents for
   broad exploration.
4. After completing a milestone, run its **verify** step. Update Status and
   append to Log.
5. If verify fails, attempt to fix. If unresolvable, record `blocked` in
   Status and stop.
6. Do not make changes outside the current milestone's scope.
7. Sub-agents may run exploration in parallel. Code writes are single-lane
   (one agent writes at a time).
8. Respect `policy/workflow.toml` budget limits (`[slice_budget]`,
   `[review_triggers]`).

## Workflow

1. Read `tasks/<slug>/BRIEF.md` → find next milestone from Status.
2. Explore relevant code (sub-agents if broad).
3. Implement changes for the milestone.
4. Run the milestone's verify step.
5. Update BRIEF.md: move milestone to `done`, set next `current`, append Log.
6. Commit if the user has requested it or the milestone is a natural
   commit point.

## Session Resumption

Read `BRIEF.md` → Status tells you exactly where to continue. No external
state files needed.
