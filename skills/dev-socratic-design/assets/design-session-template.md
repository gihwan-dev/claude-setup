# Design: [TITLE]

> Mode: [architecture | bugfix-strategy | refactor | feature]
> Status: [charter | frame | evidence-gap | system-model | alternatives | adversarial-review | decision | plan | quality-gate | done | blocked]
> Created: [DATE]

## Purpose / Big Picture

[One paragraph describing what this design addresses and why it matters.]

## Problem Framing

### Goal

[Specific, measurable goal.]

### Constraints

- [Hard constraint 1]
- [Hard constraint 2]

### Non-goals

- [Explicitly out of scope 1]
- [Explicitly out of scope 2]

### Success Criteria

- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]

## Evidence Gaps

| Gap | Status | Resolution |
|-----|--------|------------|
| [What we didn't know] | resolved / open / blocked | [How it was resolved or why it's blocked] |

## Current System Model

[Describe the relevant part of the current system: components, data flow, boundaries, invariants. Use diagrams if helpful.]

## Alternatives Considered

### Alternative A: [Name]

- Description: [What this approach does]
- Strengths: [Why it's good]
- Weaknesses: [Why it's risky or costly]
- Trade-offs: [What you gain vs what you lose]

### Alternative B: [Name]

- Description:
- Strengths:
- Weaknesses:
- Trade-offs:

## Chosen Direction

**Selected**: [Alternative name]

**Why**: [Rationale tied to constraints and trade-offs]

**Rejected alternatives**:
- [Alternative name]: [Rejection reason]

## Risks / Failure Modes

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| [Failure scenario] | [What breaks] | [high/medium/low] | [How to prevent or recover] |

## Validation Plan

- [ ] [What to test and how]
- [ ] [What signals indicate success]
- [ ] [What signals indicate failure]

## Rollback Strategy

[How to undo or revert if the chosen approach fails in production.]

## Decision Log

| Turn | State | Decision | Rationale |
|------|-------|----------|-----------|
| 1 | charter | Mode: [X] | [Why this mode] |

## Assumption Ledger

| # | Assumption | Status | Source | Challenged? |
|---|-----------|--------|--------|-------------|
| 1 | [What we assume] | verified / likely / unverified | [Evidence source] | [yes/no + turn #] |

## Open Questions

| Question | Reason | Owner / Next Step |
|----------|--------|-------------------|
| [What remains unanswered] | [External dependency / needs user input] | [Who resolves it] |

## Quality Gate Result

**Verdict**: [proceed / proceed-with-advisory / return-and-fix]

| # | Criterion | Score | Note |
|---|-----------|-------|------|
| 1 | Goal clarity | | |
| 2 | Success criteria | | |
| 3 | System model | | |
| 4 | Alternatives compared | | |
| 5 | Decision reasoning | | |
| 6 | Failure modes | | |
| 7 | Assumption ledger | | |
| 8 | Rollback strategy | | |
| 9 | Validation plan | | |
| 10 | Open questions | | |
