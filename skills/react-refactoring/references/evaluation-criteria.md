# Evaluation Criteria for Code That Is Easy to Change

Nine criteria that ground every refactoring judgment.

## 1. Minimize Change Blast Radius (Isolation)

**Question**: If this code changes, how likely is it that bugs will surface somewhere unexpected?

**Good signals**:
- Functions / modules have clear inputs and outputs
- Global-state dependency is minimal
- Side effects are managed explicitly

**Bad signals**:
- Mutable objects referenced from many places
- Implicit dependencies (for example, must be called in a specific order)
- One change triggers a chain of follow-up changes

**React context**:
- Objects passed through props are not mutated directly
- No unnecessary re-renders from Context overuse
- Custom hooks do not change external state unpredictably

---

## 2. Intent Clarity (Readability)

**Question**: Can you understand immediately what it does and why from the names and structure alone?

**Good signals**:
- Function names describe behavior precisely
- Magic numbers / strings are named as constants
- Complex conditions use explanatory variable names

**Bad signals**:
- Ambiguous names like `data`, `info`, `handler`
- Logic that is impossible to understand without comments
- A single function doing too many jobs

**React context**:
- Component names clearly express their role
- Prop names are self-descriptive
- Custom hook names communicate `use` + the meaning of what they return

---

## 3. Testability

**Question**: Can it be unit-tested without heavy environment setup?

**Good signals**:
- High ratio of pure functions
- Dependencies can be injected
- External dependencies are abstracted

**Bad signals**:
- Testing requires the entire app context
- Direct dependency on time, randomness, or the network
- You must know the internal implementation to test it

**React context**:
- Business logic is separated from the component
- Hooks can be tested without a Provider maze
- Rendering logic and data logic are separated

---

## 4. Separation of Concerns

**Question**: Are UI and business logic mixed together?

**Good signals**:
- Style changes do not require logic changes
- Data-processing logic can be reused independently
- A headless pattern could be applied cleanly

**Bad signals**:
- Complex business logic inside the component
- Styling code and state management are intertwined
- API calls and rendering live in the same function

**React context**:
- Custom hook = logic, Component = rendering
- Container / Presentational or Headless pattern
- Styling stays in a separate layer (CSS Modules, styled-components, Tailwind)

---

## 5. High Cohesion and Colocation

**Question**: Do you need to jump across many folders to change one feature?

**Good signals**:
- Related code (logic, types, styles, tests) lives physically close together
- Folder structure is organized by feature
- You can understand everything about one feature in one place

**Bad signals**:
- Splitting into `types/`, `hooks/`, `components/`, `styles/` makes files hard to find
- Related code is scattered across the repo
- Adding a feature requires touching 5+ folders

**React context**:
```text
// Good: feature-based
features/
  user-profile/
    UserProfile.tsx
    useUserProfile.ts
    userProfile.types.ts
    UserProfile.test.tsx

// Bad: layer-based
components/UserProfile.tsx
hooks/useUserProfile.ts
types/userProfile.ts
tests/UserProfile.test.tsx
```

---

## 6. Replaceability

**Question**: Can this code be detached and replaced like a Lego block?

**Good signals**:
- Clear interface / contract
- Implementation details are encapsulated
- Loose coupling between modules

**Bad signals**:
- Changing it requires "surgery"
- Changing one part forces cascading changes
- Module boundaries are unclear

**React context**:
- The component is not tightly coupled to one specific data shape
- The API layer can be swapped without rewriting the component
- Swapping a state-management library would be localized

---

## 7. Incrementality

**Question**: Can this change be split into small, incremental steps?

**Good signals**:
- It can be separated into small PRs
- Intermediate states still work
- Rollback is easy

**Bad signals**:
- Only a "big bang" refactor is possible
- Stopping halfway leaves the code broken
- The change is all-or-nothing

**React context**:
- Build the new component and replace gradually
- Use a feature flag to test the new implementation
- Extract one hook at a time

---

## 8. Consistency

**Question**: Does it fit the existing patterns and conventions of the codebase?

**Good signals**:
- Similar problems receive similar solutions
- New developers can predict behavior from established patterns
- Code style is consistent

**Bad signals**:
- A one-off pattern that exists only in this file
- Multiple ways to do the same thing
- A new pattern increases cognitive load

**React context**:
- Follow the state-management patterns the team already uses
- Respect the existing folder-structure rules
- Review current approaches before adding a new library

---

## 9. Type Leverage (TypeScript-Specific)

**Question**: Do types serve as documentation and prevent runtime errors?

**Good signals**:
- You can understand usage from the function signature alone
- Incorrect usage fails at compile time
- Types model the domain accurately

**Bad signals**:
- `any` everywhere
- Excessive type assertions (`as`)
- Type errors are discovered only at runtime
- Types do not match actual behavior

**React context**:
- Prop types document how the component is used
- Reusable hook types are expressed through generics
- State is modeled through discriminated unions

```typescript
// Good: the type models the state accurately
type LoadingState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: User }
  | { status: 'error'; error: Error }

// Bad: you only know the real state shape at runtime
type State = {
  loading: boolean;
  data: User | null;
  error: Error | null;
}
```

---

## Notes on Applying the Criteria

1. **Not every criterion must be maximized at once**: Tradeoffs exist. Prioritize based on context.

2. **Guard against over-application**: Even good principles become harmful when pushed too far. For example:
  - Over-optimizing for cohesion -> giant god modules
  - Over-optimizing for replaceability -> unnecessary abstraction layers

3. **Context rules**: Prototype code and production code should be judged differently. Consider team size and project nature.

4. **Judge improvement relative to the current state**: The key question is not whether it is ideal, but whether it is better than what exists now.
