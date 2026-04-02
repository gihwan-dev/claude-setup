---
name: build
description: >
  Execute approved phases from BRIEF.md by orchestrating Codex. Invoke when the
  user writes "build" or "$build". Claude designs prompts and orchestrates;
  Codex implements, reviews, and fixes code. Claude never writes code directly.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Build

Orchestrate Codex execution of phases from `tasks/<slug>/BRIEF.md`.

Claude is the **orchestrator**: reads files, crafts prompts, communicates with
the user, reads Codex output, and manages state. Codex is the **executor**:
writes code, runs tests, produces phase reports.

## Hard Rules

1. **Claude never writes code directly.** All code changes go through Codex.
2. If no `BRIEF.md` exists or Phases is empty, stop and suggest `$plan`.
3. One phase per invocation unless user asks to continue.
4. **Every phase must pass through the Communication Step** before Codex
   execution. No Codex invocation without user approval.
5. Codex must write a `PHASE_REPORT_<NN>.md` after each phase (enforced in
   the prompt template).
6. Claude must read the previous phase report before crafting the next prompt.
7. If Codex execution fails, report the failure. Do not implement as Claude.
8. Session resumption: read `BRIEF.md` Status + Log + all existing
   `PHASE_REPORT_*.md` files, then continue.

## Build Loop (Per Phase)

```
1. Read        — BRIEF.md + previous PHASE_REPORT_*.md
2. Craft       — Draft Codex prompt using template
3. Communicate — Present prompt to user, iterate until approved
4. Execute     — Invoke Codex
5. Review      — Read Codex output + PHASE_REPORT
6. Update      — Update BRIEF.md Status + Log
7. Checkpoint  — Ask whether to continue to next phase
```

### Step 1: Read

- Read `tasks/<slug>/BRIEF.md`, identify the current phase from `Status`.
- Read all existing `tasks/<slug>/PHASE_REPORT_*.md` files.
- Read reference documents listed in `BRIEF.md` References section.

### Step 2: Craft

Build the Codex prompt using the template at
`skills/build/references/codex-prompt-template.md`.

Fill variables:
- `PHASE_PURPOSE` ← BRIEF Phase "Purpose"
- `REFERENCE_CONTEXT` ← compressed previous phase reports + relevant doc
  excerpts + BRIEF decisions/context (target: under 500 tokens accumulated)
- `PHASE_GOAL` ← BRIEF Phase "Done when" expanded into actionable goal
- `DONE_CRITERIA` ← BRIEF Phase "Done when" + "Verification" merged
- `PHASE_REPORT_PATH` ← `tasks/<slug>/PHASE_REPORT_<NN>.md`
- `VERIFICATION_COMMANDS` ← BRIEF Phase "Verification"

### Step 3: Communicate (Required Gate)

Present the draft to the user:

```
--- Phase N: <Name> ---

BRIEF:
  Purpose: <from BRIEF>
  Done when: <from BRIEF>

Previous phase state:
  <compressed key facts from phase reports>

Codex prompt draft:
  Purpose: <filled>
  Reference context: <summary of what's included>
  Goal: <filled>
  Done criteria: <filled>
  Verification: <filled>

[1] Approve and execute
[2] Modify prompt (tell me what to change)
[3] Add context or constraints
[4] Skip this phase
```

Iterate until the user approves. On modification requests, incorporate changes
and re-present. The user may also request the full raw prompt.

### Step 4: Execute

Invoke Codex with the approved prompt via the Codex plugin runtime:

```bash
CODEX_SCRIPT=$(ls -d ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | sort -V | tail -1)
node "$CODEX_SCRIPT" task --write "<approved prompt>"
```

If the script is not found, fall back to `codex exec --full-auto "<approved prompt>"`.
If neither is available, suggest `/codex:setup`.

### Step 5: Review

- Read Codex stdout for immediate results.
- Read `tasks/<slug>/PHASE_REPORT_<NN>.md` that Codex was instructed to write.
- If the phase report is missing, extract key facts from Codex stdout as
  fallback and warn the user.
- Present a summary to the user: what was done, verification result, any
  open issues.

### Step 6: Update

- Update `BRIEF.md` Status: move completed phase to `done`, advance `current`.
- Append to `BRIEF.md` Log: date + what was completed + any issues.

### Step 7: Checkpoint

Summarize progress and ask whether to continue to the next phase.

## Reference Document Integration

- Read all documents listed in `BRIEF.md` References before each prompt.
- For Socratic design docs: extract "Chosen Direction", "Decisions", "Risks",
  and "Constraints" sections.
- For previous phase reports: compress to key facts. Most recent 2-3 in detail;
  older ones as 1-2 lines each. Target: under 500 tokens accumulated.
- Users can add arbitrary reference documents during the Communication Step.

## Phase Report Format

See `skills/build/references/phase-report-format.md` for the full spec.
Codex writes `tasks/<slug>/PHASE_REPORT_<NN>.md` after each phase.

## Error Handling

- **Codex timeout**: Report timeout. Suggest retrying with adjusted prompt or
  splitting the phase.
- **Codex failure**: Report the error. Do not fall back to Claude implementation.
- **Phase report missing**: Warn user. Extract what's available from stdout.
- **Verification failure reported by Codex**: Present the failure. Ask user
  whether to retry (re-invoke Codex with fix instructions) or mark blocked.

## Session Resumption

Read `BRIEF.md` Status + Log + all `PHASE_REPORT_*.md` → identify where to
resume → continue from that phase.
