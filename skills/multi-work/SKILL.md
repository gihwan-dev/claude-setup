---
name: multi-work
description: >
  Manager-style multi-agent orchestration utility. Use when the user writes
  "/multi-work", "$multi-work", or when a task requires multi-agent exploration
  before deciding the execution strategy. Explores first with 2+ helpers, then
  records an Orchestration Strategy the main thread must follow. Do not use for
  simple single-file tasks, when the scope is already clear, or for tasks that
  do not benefit from parallel exploration.
allowed-tools: Read, Grep, Glob, Agent
---

# Multi Work

This is an explicit multi-agent orchestration utility.
Always start with multi-agent exploration, then decide whether the main thread should stay a pure orchestrator, stop with `split-replan`, or decompose independent work units.

## Trigger

- `/multi-work`
- `$multi-work`
- `multi-work`

## Hard Rules

- Always begin with multi-agent exploration. Use at least 2 helpers.
- If multi-agent fan-out is unavailable in the runtime, report blocked instead of collapsing to single-agent work.
- Before helper results return, do not read more files, run more searches, or continue exploration beyond `wait` and result collection.
- After helper fan-out, the main agent does not do parallel side work. Any follow-up exploration happens only after results return and stays minimal.
- The main agent synthesizes helper output instead of re-reading the repository. Treat helper output as the primary evidence surface after fan-out.
- In planning or collaborator modes, the output must contain an `Orchestration Strategy` section.
- Use decomposition only when the work can be framed as 2 or more independent work units with clear acceptance and merge boundaries.
- Shared-file edits, final integration, and final validation stay with designated execution lanes, not with ad hoc main-thread fallback.
- The `Orchestration Strategy` must state helper combination, execution owner, allowed main-thread actions, fallback policy, and review boundary.
- Keep helper selection, decomposition thresholds, and execution guardrails aligned with `policy/workflow.toml`, `scripts/workflow_contract.py`, and this skill's orchestration contract.
- Do not auto-run review. Keep multi-agent review as a separate explicit `multi-review` step.
- When helper results indicate low confidence or blocked status, follow the escalation response matrix in the routing contract instead of proceeding optimistically.

## Workflow

0. **Scope Gate**: If the request is ambiguous or acceptance criteria are unclear, ask the user a scoping question before helper fan-out. Skip this step when the request is concrete.
1. Read `${SKILL_DIR}/references/routing-contract.md` and choose the helper combination that matches the request type.
2. Always execute multi-agent exploration first.
3. After helper fan-out, do only `wait` and result collection until results return. Pause additional file reads and searches in the main agent.
4. After helper results return, synthesize their structured output into an `Orchestration Strategy`.
5. If the runtime is in planning or collaborator mode, make `Orchestration Strategy` an explicit output section. It must include `Helper plan`, `Execution owner`, `Allowed main-thread actions`, `Fallback`, and `Review boundary`.
6. Decide whether the work should stay local, stop for `split-replan`, or decompose into independent work units.
7. Decompose only when each work unit has a clear owner, a clear output boundary, and limited dependency on sibling units.
8. Keep shared-file integration and final validation with the designated integration or verification lane instead of pushing them into ad hoc main-thread work.
9. If review is needed after execution, leave an explicit `multi-review` next step instead of auto-running it.

## Required References

- helper matrix, orchestration matrix, and decomposition guardrails: `${SKILL_DIR}/references/routing-contract.md`

## Validation

- Confirm the helper set contains at least 2 agents.
- Confirm the main agent does not continue file reads or searches between helper fan-out and result collection.
- Confirm helper output is synthesized into an `Orchestration Strategy` instead of triggering broad repository rereads.
- Confirm planning or collaborator mode output includes `Orchestration Strategy` with helper combination, execution owner, allowed main-thread actions, fallback, and review boundary.
- Confirm decomposition is used only for independent work units with clear merge boundaries.
- Confirm shared-file integration and final validation remain assigned to designated execution lanes instead of broad main-thread fallback.
- Confirm execution closeout does not auto-run review.
