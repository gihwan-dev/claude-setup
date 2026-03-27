# Test Engineer Review Playbook

## Review Order

- Inspect added or changed tests before asking for new coverage.
- Separate `test quality` from `test gap`.
- Ask what real regression each test blocks, and whether an existing test already blocks the same regression.

## Review Lens

- Confidence > Coverage
- Behavior > Implementation
- Evaluate both regression-catching sensitivity and specificity that avoids noisy false positives.
- Fewer, stronger tests > more, noisier tests.

## Disposition Vocabulary

- `keep`: the test provides meaningful regression protection.
- `merge`: scenarios overlap and the verification can be consolidated.
- `rewrite`: implementation coupling, weak assertions, or excessive mocking dominate.
- `delete`: the test is close to a tautological assertion, liar test, or rechecks deleted behavior.
- Default to `delete` or `merge` when incremental regression signal is close to zero.

## Sensitive Smells

- Tautological assertions or implementation mirroring
- Internal-state or private-method coupling
- Excessive mocking
- Weak assertions
- Snapshot overuse
- Duplicate or scenario-fragmented tests
- Hallucinated constraints
- Flaky timing dependence

## Reporting Contract

- Every material `test quality` finding includes a disposition and the regression risk the current test does or does not block.
- Use `test gap` only when behavior genuinely lacks coverage after the changed tests were triaged.
