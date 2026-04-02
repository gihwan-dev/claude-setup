---
name: plan
description: >
  Read-only planning skill. Invoke when the user writes "plan" or "$plan".
  Explores the codebase, clarifies requirements with the user, and produces
  a single abstract BRIEF.md under tasks/<slug>/. The brief focuses on what
  and why — not how. Implementation details are left to Codex during build.
allowed-tools: Read, Grep, Glob, Write, Agent
---

# Plan

Turn a user request into a clear, abstract `tasks/<slug>/BRIEF.md`.

The brief is a **design document**, not an implementation spec. It defines
goals, constraints, phases, and success criteria. Codex decides implementation
details during `$build`.

## Hard Rules

1. No code edits. Read-only exploration only.
2. Produce exactly one file: `tasks/<slug>/BRIEF.md`.
3. If `BRIEF.md` already exists, update it in place.
4. If `docs/ai/ENGINEERING_RULES.md` exists, reference it for design choices.
5. Phases must be specific, independently verifiable, and ordered.
6. Ask the user when ambiguous — batch up to 3 questions at a time.
7. For broad/unclear scope, use **scoped read sub-agents**; do not let one
   agent wander the whole repo without boundaries.
8. Phases describe **what** and **why**, not **how**. Do not prescribe
   implementation approach, file structure, or code patterns. Codex decides.
9. If a Socratic design document exists (`docs/design/<slug>.md`), reference
   it in the `References` section and incorporate its decisions/constraints.
10. Each phase's `Inputs` must list specific files or docs Codex needs to read.

## BRIEF.md Format

```markdown
# <Task Title>

## Goal
What we are achieving and why it matters. (1-3 sentences)

## Context
- Current state of the system relevant to this task
- Key constraints (technical, business, timeline)
- Reference documents: (paths to design docs, specs, etc.)

## Scope
- In scope: (bullet list)
- Out of scope: (bullet list)
- Do not touch: (specific files/areas)

## Success Criteria
- [ ] Testable criterion 1
- [ ] Testable criterion 2

## Phases
Ordered list. Each phase is a coherent deliverable unit.

### Phase 1: <Name>
- **Purpose**: What this phase achieves (1-2 sentences)
- **Inputs**: What Codex needs to know (files, context, decisions)
- **Done when**: Observable outcome that proves completion
- **Verification**: Commands or checks to confirm

### Phase 2: <Name>
...

## Decisions
Key technical/design decisions made during planning.
- Decision 1: <what> — <why>

## Risks
| Risk | Mitigation |
|------|-----------|
| ... | ... |

## References
- docs/design/<slug>.md (if Socratic design was used)
- <any other relevant docs>

## Status
- current: (phase name or "not started")
- done: (list)
- blocked: (if any, with reason)

## Log
(append-only: date + event)
```

## Workflow

1. Locate or create `tasks/<slug>/BRIEF.md`.
2. Map uncertainty: what is known vs unknown.
3. Dispatch scoped discovery sub-agents for unknowns (parallel when independent).
4. Synthesize findings and ask clarifying questions if needed.
5. Write/update `BRIEF.md` — abstract phases, no implementation detail.
6. Present to the user for confirmation.

## Session Resumption

Read `tasks/<slug>/BRIEF.md` → check `Status` and `Log` → continue.
