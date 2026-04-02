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

## Codex Plugin Skills (세션당 1회 로드)

Build 시작 시 Skill 도구로 아래 플러그인 스킬을 로드한다:

1. `codex:gpt-5-4-prompting` — 프롬프트 구조, XML 블록 규칙, 레시피
2. `codex:codex-cli-runtime` — Codex 호출 명령어, 플래그, 실행 규칙

로드된 스킬이 제공하는 호출 계약과 프롬프트 규칙을 따른다.
로드 실패 시 `${SKILL_DIR}/references/codex-prompt-template.md`를 fallback.

## Build Loop (Per Phase)

```
0. Bootstrap   — Codex plugin skills 로드 (세션당 1회)
1. Read        — BRIEF.md + previous PHASE_REPORT_*.md
2. Craft       — Draft Codex prompt
3. Communicate — Present prompt to user, iterate until approved
4. Execute     — Invoke Codex (codex:codex-cli-runtime 계약에 따라)
5. Review      — Read Codex output + PHASE_REPORT
6. Update      — Update BRIEF.md Status + Log
7. Checkpoint  — Ask whether to continue to next phase
```

### Step 1: Read

- Read `tasks/<slug>/BRIEF.md`, identify the current phase from `Status`.
- Read all existing `tasks/<slug>/PHASE_REPORT_*.md` files.
- Read reference documents listed in `BRIEF.md` References section.

### Step 2: Craft

`codex:gpt-5-4-prompting`의 XML 블록 규칙과
`${SKILL_DIR}/references/codex-prompt-template.md`의 변수 구조를 결합하여
Codex 프롬프트를 작성한다.

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

`codex:codex-cli-runtime`에서 로드된 호출 계약에 따라 Codex를 실행한다.
`--write` 플래그로 쓰기 가능 모드로 실행.

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
