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

An orchestration utility that dispatches helpers first, then synthesizes their
findings into a strategy the main thread follows. The core idea: the main thread
should never build its own understanding of the codebase when helpers can do it
in parallel with fresh context windows.

## Workflow

0. **Scope Gate** — If the request is ambiguous or acceptance criteria are unclear, ask the user a scoping question before dispatching helpers. Skip when the request is concrete.
1. Read `${SKILL_DIR}/references/routing-contract.md` and choose the helper combination that matches the request type.
2. Dispatch at least 2 helpers. If the runtime does not support multi-agent fan-out, report blocked instead of falling back to single-agent work (single-agent work defeats the purpose of context isolation).
3. **Wait** — Do not read files, run searches, or explore the repo while helpers are running. The main thread exploring in parallel builds a second context that conflicts with helper evidence, leading to inconsistent synthesis.
4. Synthesize helper output into an **Orchestration Strategy**. Treat helper output as the primary evidence surface; re-reading the repository after fan-out is a failure mode because it replaces structured evidence with unfiltered noise.
5. When helpers report low confidence or blocked status, follow the escalation response matrix in the routing contract instead of proceeding optimistically.
6. Decide the execution mode:
   - **Keep local** — when shared-file edits or sequencing dependencies dominate.
   - **`split-replan`** — when acceptance boundaries are still unclear after exploration, or the work is too broad to bound.
   - **Decompose** — only when 2+ independent work units each have a clear owner, a clear output boundary, and limited sibling dependency. Shared-file integration and final validation stay with designated execution lanes, not ad hoc main-thread fallback.
7. If review is needed after execution, leave an explicit `multi-review` next step. Auto-running review conflates orchestration and evaluation, making it harder to trace which step introduced issues.

## Orchestration Strategy Output

In planning or collaborator modes, the output must include an `Orchestration Strategy` section. This section is the handoff contract between exploration and execution.

Required fields:
- **Helper plan** — which helpers were used and why
- **Execution owner** — who executes (keep-local, worker lanes, csv-fanout)
- **Allowed main-thread actions** — what the main thread may do beyond synthesis
- **Fallback** — what happens when a lane blocks
- **Review boundary** — who reviews, when, and whether `multi-review` is the next step

### Example

```
## Orchestration Strategy

- Helper plan: explorer + structure-reviewer (basic code exploration),
  web-researcher added for external API docs
- Execution owner: keep-local (2 files share state, not decomposable)
- Allowed main-thread actions: synthesize helper output, write Orchestration
  Strategy, update STATUS.md
- Fallback: if web-researcher returns low confidence on API docs,
  split-replan and ask user for doc links
- Review boundary: after implementation, explicit multi-review
```

## Required References

- Helper matrix, escalation matrix, timeout policy, conflict resolution, orchestration matrix, decomposition guardrails: `${SKILL_DIR}/references/routing-contract.md`

## Alignment

Keep helper selection, decomposition thresholds, and execution guardrails aligned with `${SKILL_DIR}/references/routing-contract.md`. When you are working inside this repository, repo-maintenance policy files such as `policy/workflow.toml` can provide extra maintainer context, but installed skill runs must not depend on repo-root helpers.
