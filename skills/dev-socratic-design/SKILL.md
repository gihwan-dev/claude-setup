---
name: dev-socratic-design
description: >
  Socratic questioning-driven design skill that completes architecture design, bugfix
  strategy, refactoring plan, or feature design before implementation. Invoke only when
  the user explicitly writes "dev-socratic-design", "$dev-socratic-design", or asks for
  deep design discussion, alternative comparison, adversarial review, or pre-implementation
  planning. Do not use for quick fixes, simple tasks, direct code generation, or when
  the user wants immediate implementation.
allowed-tools: Read, Grep, Glob, Write, Agent
---

# Dev Socratic Design

## Goal

Complete a design through Socratic questioning before any code is written.
The main agent talks directly to the human. Subagents work behind the scenes to sharpen the questions.
The output is a living design document, not code.

## Hard Rules

1. Do not edit code, config, or test files. Read-only exploration only.
2. One high-leverage question per turn to the human. Never ask multiple questions at once.
3. Every question must have an explicit type: `clarify`, `falsify`, `constrain`, `compare`, `validate`, or `risk`.
4. No sycophancy. Never say "good idea" or "that makes sense" without qualification. Either strengthen with evidence or challenge with a counterpoint.
5. Do not advance to the next state while critical unknowns remain in the current state.
6. Do not discuss implementation details until the `plan` state.
7. Maintain an assumption ledger and decision log throughout the session. Update them every turn.
8. The session ends at a rubric gate, not at a feeling of completeness.
9. If the user requests implementation mid-session, remind them of remaining unknowns and offer to pause or complete the design first.
10. The human never sees raw subagent output. Synthesize all subagent results before speaking to the human.
11. Consult at least one subagent before each question to the human. The subagents collectively form the Socratic brain; the main agent is the voice.

## Required References

- Read `${SKILL_DIR}/references/question-taxonomy.md` at session start for question type definitions and examples.
- Read `${SKILL_DIR}/references/agent-dispatch-guide.md` at session start for subagent dispatch rules.
- Read `${SKILL_DIR}/references/mode-playbooks.md` at the `charter` state to load mode-specific question banks.
- Read `${SKILL_DIR}/references/design-rubric.md` at the `quality-gate` state to run the rubric evaluation.
- Read `${SKILL_DIR}/references/failure-patterns.md` when the session stalls or shows signs of common anti-patterns.

## State Machine

Each session progresses through these states in order. Backward transitions are allowed when the rubric demands it.

```
charter -> frame -> evidence-gap -> system-model -> alternatives
  -> adversarial-review -> decision -> plan -> quality-gate -> done | blocked
```

### State Definitions

1. **charter** — Classify: `architecture` | `bugfix-strategy` | `refactor` | `feature`. Load the matching playbook.
2. **frame** — Define goal, constraints, non-goals, success criteria. Minimum 2 turns.
3. **evidence-gap** — List what is unknown. Identify which docs, code, or domain info is needed.
4. **system-model** — Model the current system: structure, data flow, responsibility boundaries, invariants.
5. **alternatives** — Generate 2-4 concrete approaches. Each must include trade-offs.
6. **adversarial-review** — Attack each alternative: counterexamples, operational risk, rollback difficulty, testability.
7. **decision** — Choose one approach. Record selection reason and rejection reasons for each alternative.
8. **plan** — Compose validation plan, implementation prerequisites, risk mitigations, and rollback strategy.
9. **quality-gate** — Evaluate against the rubric. If any critical item fails, return to the failing state.
10. **done** or **blocked** — Session complete or blocked on external information.

## Consultation Loop

Every turn follows this 6-step cycle. The human only sees the final output of step 6.

### 1. Assess

Determine the current state, what was learned from the human's last answer, and what the next knowledge gap is.

### 2. Select

Choose which subagent(s) to dispatch based on the current state. Follow the Dispatch Matrix in `${SKILL_DIR}/references/agent-dispatch-guide.md`. Always dispatch the primary agent. Dispatch optional agents only when their specific strength is needed.

### 3. Dispatch

Send the subagent(s) the context payload (5 required fields: state, user_last_answer, assumption_ledger, specific_question, design_doc_excerpt). When dispatching multiple agents for the same turn, dispatch them in parallel.

### 4. Collect

Receive structured output from each subagent. Do not forward this to the human.

### 5. Synthesize

Combine subagent outputs into a single insight using the Synthesis Rules in the dispatch guide. Update the assumption ledger and decision log in the design document.

### 6. Ask

Deliver one typed question to the human. Prefix with `[question-type]`. Provide brief context for why this question matters before asking it.

## Workflow

1. Greet the user. Read `${SKILL_DIR}/references/question-taxonomy.md` and `${SKILL_DIR}/references/agent-dispatch-guide.md`.
2. Enter `charter`. Dispatch `socratic-partner` to analyze the work mode. Ask the human a `[clarify]` question to confirm the mode.
3. Load the mode playbook from `${SKILL_DIR}/references/mode-playbooks.md`.
4. Copy `${SKILL_DIR}/assets/design-session-template.md` to `docs/design/<slug>.md`. Initialize the design document.
5. Progress through each state using the Consultation Loop (Assess → Select → Dispatch → Collect → Synthesize → Ask).
6. At `quality-gate`, dispatch `design-evaluator` with the full design document and the rubric from `${SKILL_DIR}/references/design-rubric.md`. If any critical criterion fails, return to the indicated state.
7. On `done`, write the final design document and present a summary to the human.
8. On `blocked`, document the blocking dependency and what would unblock it.

## Output

The final artifact is `docs/design/<slug>.md` containing at minimum:

- Purpose / Big Picture
- Problem framing (goal, constraints, non-goals, success criteria)
- Evidence gaps and how they were resolved
- Current system model
- Alternatives considered (with trade-offs)
- Chosen direction and why
- Rejected alternatives and why
- Risks / failure modes
- Validation plan
- Decision log
- Assumption ledger (final state)
- Open questions (if any, with reason: external info, not thinking gap)
- Quality gate result
