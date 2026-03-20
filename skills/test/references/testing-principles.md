# What Makes a Good Test?

## 1. Why Tests Exist

Tests exist for **confidence**, not for coverage.

- A false-positive test that passes while the feature is broken is **more dangerous** than having no test at all because it creates false confidence.
- The value formula for a test is: write it only when **`confidence gained > maintenance cost`**.
- The goal is not to attach tests to every function. Ask first: "Without this test, when would we discover the problem?"

## 2. Properties of a Good Test

A good test satisfies two properties at the same time:

| Property | Meaning | Failure mode when missing |
|-----|------|------------|
| **Sensitivity** | It fails when the feature breaks | It passes even when there is a bug (false positive) |
| **Specificity** | It survives implementation refactors | It must be rewritten on every refactor (false negative) |

High sensitivity only: snapshots — they fail on irrelevant changes.
High specificity only: `expect(result).toBeTruthy()` — almost anything passes.

## 3. Test Behavior, Not Implementation

### What to test

- What a user can observe: rendered output, reaction to events, callback invocations
- The input → output relationship of a function
- The contract of a public API

### What not to test

- Internal state (such as inspecting `useState` values directly)
- Private methods
- Framework / library behavior (React rendering, TanStack Table internals)

### Decision rule

> "If I change the internal implementation of this code, would this test break?"

If yes, it is coupled to implementation. When behavior stays the same but the test still breaks, that test is an enemy of refactoring.

## 4. Choose the Right Test Boundary

| Target | Suitable test | Why |
|------|-------------|------|
| Pure functions / utilities | Unit (`*.spec.ts`, `*.test.ts`) | Fast and good for edge cases |
| User interaction / rendered output | Browser test (`*.browser.test.tsx`) | Needs validation in a real DOM |
| Feature combinations | Browser test | Only meaningful in an integrated environment |
| Custom Feature state logic | Unit (`*.spec.ts`) | Fast verification with a mock table |

## 5. Arrange-Act-Assert (AAA)

Every test should follow three steps:

```typescript
// Arrange: prepare only what the test needs
const { container } = render(<Default />);
await wait(RENDER_WAIT_TIME);
const tester = new TableTester(container);

// Act: perform one user action
fireEvent.click(tester.getSortButton('Name'));

// Assert: verify the expected result
expect(tester.getColumnValues(1)).toEqual(['Alice', 'Bob', 'Charlie']);
```

- Arrange should set up **only the minimum** needed for the test.
- Act should perform **one action**.
- Assert should validate **concrete values**.

## 6. Names Are Read When Tests Fail

When a test fails, the first thing people read is the test name.

```typescript
// ✅ You can tell immediately what broke
it('sorts ascending when the sort button is clicked')
it('shows an empty-state message when the dataset is empty')
it('disables the move-down button on the last row')

// ❌ You must read the test body to understand it
it('test case 1')
it('works normally')
it('does not throw an error')
```

**Pattern: `[condition] -> [result]`** or `when [situation], [result]`

## 7. Minimal Setup Principle

- Prepare **only what this test needs**.
- Excessive setup hides what the test is actually validating.
- Extract shared setup into helpers / factories when needed, but **keep each test's intent visible**.

```typescript
// ❌ Overloaded setup — why does a sorting test include selectable and pagination?
const options = {
  sortable: { use: true },
  selectable: { use: true, mode: 'multiple' },
  pagination: { use: true, pageSize: 10 },
};

// ✅ Only what the sorting test needs
const options = { sortable: { use: true } };
```

## 8. Assertion Quality

```typescript
// ❌ Meaningless assertions: no useful information on failure
expect(result).toBeTruthy();
expect(rows.length > 0).toBe(true);
expect(element).toBeDefined();

// ✅ Specific assertions: expected vs actual is obvious on failure
expect(tester.renderedRowCount).toBe(5);
expect(tester.getColumnValues(1)).toEqual(['Bob', 'Charlie', 'Alice']);
expect(header).toHaveAttribute('aria-sort', 'ascending');
```

**Rules:**
- Compare concrete values instead of using `toBeTruthy()` / `toBeDefined()`
- Do not convert values into booleans such as `rows.length > 0`; compare `rows.length` directly
- Use `toEqual` for arrays so order is verified too

## 9. Selector Priority

Use this priority order when locating DOM elements:

1. **Accessibility attributes**: `role`, `aria-label`, `aria-sort`, `aria-checked`
2. **Semantic HTML**: `button`, `heading`, `table`
3. **Data attributes**: `data-testid`, `data-pinned`, `data-index`
4. **Text content**: `getByText`, `textContent`
5. **Class names**: **last resort** — breaks when styles change

If a Page Object Model helper exists (for example `TableTester`), do not reach for raw selectors directly. Go through the helper.

## 10. Anti-Patterns

| Anti-pattern | Problem | Better alternative |
|---------|--------|------|
| Testing framework behavior | React / TanStack already test that | Test only business logic |
| Snapshot overuse | Fails on irrelevant changes | Use specific assertions |
| Boolean assertions | Failure message is meaningless | Compare concrete values |
| Copy-pasted tests | Maintenance nightmare | Extract helpers / page objects |
| Excessive mocking | Drifts away from real behavior | Mock only the minimum necessary |
| Implementation coupling | Breaks on refactor | Use behavior-based tests |
| Multiple scenarios in one `it` | Failure cause becomes ambiguous | One scenario per `it` |
| Creating test data inside the test | Drifts from story data | Reuse story args |
| Direct `querySelector` usage | Selector changes ripple everywhere | Use helper classes |
| Loop-generated / dynamic tests | Harder to read | Write each case explicitly |
