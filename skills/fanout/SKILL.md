---
name: fanout
description: >
  General-purpose 3-phase parallel execution primitive (Read → Write → Review).
  Decomposes a task into work items via CSV, fans out read agents in parallel,
  executes writes sequentially, then fans out review agents in parallel. Invoke
  with "$fanout". Do not use for single-file changes or tasks that don't
  benefit from decomposition.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Fanout

Decompose a task into parallel work items and execute them through a 3-phase
pipeline: **Read** (parallel) → **Write** (sequential) → **Review** (parallel).

## Trigger

- `$fanout`
- `/fanout`

## Hard Rules

1. Read and Review phase sub-agents are read-only. No code edits.
2. Write phase runs single-lane. The main agent executes all writes
   sequentially. Never delegate writes to sub-agents.
3. After Decompose, pause for user approval before Phase 1.
4. Respect `policy/workflow.toml` budget:
   `max_helpers_per_fanout` (default 4) and
   `max_total_fanouts_per_session` (default 3).
5. If Phase 1 read findings suggest the write plan should change, notify the
   user and adjust before proceeding to Phase 2.
6. Failed rows get 1 retry with error context appended. After a second failure,
   mark as `skipped`. Stop the pipeline if overall success rate drops below 50%.
7. Use a single `work-items.csv` with a `phase` column to distinguish
   read / write / review rows.
8. Each sub-agent prompt follows the Dispatch Prompt Contract in
   `references/dispatch-prompts.md`. No orchestration details leak to helpers.

## Input

The user describes the task directly. Fanout decomposes and executes it.

## Workflow

### Step 0: Intake

Collect from the user's request:
- Task description
- Target scope (files, directories, modules)

### Step 1: Decompose

1. Explore the codebase to understand the scope. Use sub-agents for broad
   exploration if needed.
2. Identify independent work units that benefit from parallel read/review.
3. Generate `work-items.csv` following the schema in
   `${SKILL_DIR}/references/csv-schema.md`.
4. Ensure every write row has `agent_type=main`.
5. Link dependencies: write rows reference read rows, review rows reference
   write rows via `depends_on`.

### Step 2: Approve (Mandatory Gate)

Present the decomposition to the user:

```
Fanout decomposition: {task_name}

Read phase:  {N} items — {agent types}
Write phase: {N} items — sequential
Review phase: {N} items — {agent types}

Total helpers: {N} (budget: {max_helpers_per_fanout})
```

Wait for approval. If the user requests changes, update `work-items.csv` and
re-present.

### Step 3: Phase 1 — Read Fan-out

1. Filter `phase=read` rows from `work-items.csv`.
2. Dispatch sub-agents in parallel, up to `max_helpers_per_fanout` at a time.
   If more rows exist, batch them.
3. Each agent explores `target_paths` per its `instruction`.
4. Collect results into `output_ref` paths (`.fanout-cache/{row_id}.md`).
5. Update `status` column for each row.
6. If findings suggest write plan changes, notify the user before Phase 2.

Read agents follow the return shape defined in
`${SKILL_DIR}/references/phase-contract.md`.

### Step 4: Phase 2 — Write Lane

1. Filter `phase=write` rows, sort by `depends_on` topological order.
2. For each write row, sequentially:
   a. Read the `output_ref` files from dependent read rows.
   b. Execute the `instruction` — edit, create, or refactor code.
   c. Update `status` to `success` or `failed`.
3. On failure: retry once with error context. If still failing, mark `skipped`
   and continue to the next write row.

### Step 5: Phase 3 — Review Fan-out

1. Filter `phase=review` rows from `work-items.csv`.
2. Dispatch review agents in parallel, up to `max_helpers_per_fanout`.
3. Each agent reviews the files changed in Phase 2 per its `instruction`.
4. Collect results into `output_ref` paths.
5. Update `status` column.

### Step 6: Synthesize

Aggregate all phase results into a summary:

```
Fanout complete: {task_name}

[Phase 1 — Read]
- Dispatched: {N} agents
- Success: {N}, Failed: {N}, Skipped: {N}
- Key findings: {bullet list}

[Phase 2 — Write]
- Executed: {N} items (sequential)
- Success: {N}, Failed: {N}, Skipped: {N}
- Files changed: {list}

[Phase 3 — Review]
- Dispatched: {N} agents
- Findings: {count by severity}
- Critical issues: {list or "none"}

```

## Failure Recovery

Follow the rules in `${SKILL_DIR}/references/phase-contract.md`:

- Per-row: 1 retry with error context, then `skipped`
- Phase-level: stop if success rate < 50%
- Budget exhaustion: do not exceed `max_total_fanouts_per_session`

## Session Resumption

Read `work-items.csv` `status` column to determine progress. Resume from the
first `pending` row in the current phase.

## Required References

- CSV schema: `${SKILL_DIR}/references/csv-schema.md`
- Phase data contracts: `${SKILL_DIR}/references/phase-contract.md`
- Dispatch prompt templates: `${SKILL_DIR}/references/dispatch-prompts.md`
- Budget limits: `policy/workflow.toml` `[orchestration_budget]`

