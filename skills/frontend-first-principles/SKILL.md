---
name: frontend-first-principles
description: >
  First-principles decision support for frontend feature planning and UI flow changes before implementation.
  Use when planning a frontend feature or UI flow, when requirements are vague or overloaded with assumptions,
  when validating whether a proposed frontend approach is actually right, or when tradeoff analysis is needed before coding.
  Do not use for trivial code edits, known-root-cause bugs, or syntax/type/mechanical refactor-only tasks.
---

# Frontend First Principles

Validate frontend decisions before implementation. Decompose the requirement, strip away assumptions, and choose the simplest workable solution.

## Language Rule

- Always respond in the user's language.
- Keep code identifiers, file paths, APIs, and commands in their original language.

## Workflow

1. Restate the user goal in one sentence from the end-user perspective.
2. Separate hard constraints from assumptions, conventions, and inherited patterns.
3. Ask only the minimum number of high-leverage questions when missing information would materially change the solution.
4. Inspect the repository first before asking unnecessary questions. Check relevant routes, components, hooks, state management, API contracts, and design tokens when available.
5. Extract frontend first principles:
   - user intent
   - source of truth for data
   - rendering constraints
   - interaction constraints
   - accessibility constraints
   - performance constraints
6. Generate 2 to 4 solution directions.
7. Compare options on simplicity, maintainability, accessibility, performance, and UX risk.
8. Recommend one path and explain the decision in plain terms.
9. Produce an implementation-ready plan with concrete file-level steps.

## Decision Rules

- Prefer the simplest viable solution over abstract architecture.
- Reject options that add indirection without clear user or maintenance value.
- Call out uncertainty explicitly instead of hiding it in assumptions.

## Required Output Format

Use the exact section order below:

1. Goal
2. Hard Constraints
3. Assumptions to Challenge
4. First Principles
5. Options
6. Recommendation
7. Implementation Plan
8. Risks / Edge Cases
9. Validation Checklist

## When Not To Use This Skill

- Trivial single-file edits with clear implementation path.
- Bugs with already known root cause and direct fix.
- Syntax fixes, typing fixes, import cleanup, or mechanical refactors.

## Example Invocations

- `$frontend-first-principles I want to change the checkout-step UI flow. Review whether the current structure is right before we implement anything.`
- `$frontend-first-principles Compare the tradeoffs of this React state-management approach and tell me whether it is overengineered or if there is a simpler alternative.`
- `$frontend-first-principles The requirements are vague. Separate hard constraints from assumptions and turn that into an implementation plan before coding.`
