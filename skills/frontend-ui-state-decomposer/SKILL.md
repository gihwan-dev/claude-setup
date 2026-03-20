---
name: frontend-ui-state-decomposer
description: >
  Turn vague frontend feature requirements into an explicit UI state model, event transition map,
  component boundary plan, and pre-implementation test checklist.
  Use when designing a page, component, form, modal, table, onboarding flow, checkout flow, or dashboard interaction,
  especially when requirements are feature-oriented but the UI state model is not explicit,
  or when the user wants to identify edge cases before coding.
  Do not use for backend-only tasks, pure debugging, or when the UI state model is already fully specified and implementation-ready.
---

# Frontend UI State Decomposer

Break vague frontend requirements into a state-centered model before implementation. Make state, events, and boundaries explicit first so omissions and rework decrease.

## Language Rule

- Always respond in the user's language.
- Keep code identifiers, file paths, APIs, and commands in their original language.

## Workflow

1. Identify user intents and success criteria from the end-user perspective.
2. Determine the minimum required data and source of truth.
3. Enumerate UI states.
   - Always evaluate: initial, loading, refreshing, empty, partial, error, success, disabled, permission denied, offline, optimistic, stale.
   - Do not skip empty/error/loading states even when they look obvious.
   - Prefer fewer states and simpler transitions when possible. Merge redundant states with identical UI behavior.
4. Map events and state transitions.
5. Define component boundaries and responsibilities.
   - container vs presentational
   - server state vs client state
   - local state vs shared state
6. Call out accessibility, responsive behavior, localization, and performance constraints.
7. Produce edge cases and a test checklist.

## Required Output Format

Use the exact section order below:

1. User Intents
2. Success Criteria
3. Data Contract / Source of Truth
4. State Matrix
5. Events and Transitions
6. Component Breakdown
7. A11y / Responsive / Perf Constraints
8. Edge Cases
9. Test Checklist

## Output Constraints

- In `State Matrix`, include state name, entry condition, visible UI, blocked actions, and recovery path.
- In `Events and Transitions`, include event, source state, target state, guard, and side effects.
- If critical details are missing, add a short `Assumptions` subsection and continue.
- Keep outputs implementation-ready and framework-agnostic unless the user asked for a specific stack.

## Example Invocations

- `$frontend-ui-state-decomposer The page requirements are still vague. Build the UI state model, event transitions, and test checklist before implementation.`
- `$frontend-ui-state-decomposer Before implementing this modal-based onboarding flow, break it down into state-specific UI and transition conditions.`
- `$frontend-ui-state-decomposer Organize the edge cases for this dashboard table (filters / sorting / refresh / offline) around UI state.`
