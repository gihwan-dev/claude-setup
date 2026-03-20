# Test Engineer Review Playbook

## Review Lens

- Confidence > Coverage
- Behavior > Implementation
- Evaluate both regression-catching sensitivity and specificity that avoids noisy false positives.

## Disposition Vocabulary

- `keep`: the test provides meaningful regression protection.
- `merge`: scenarios overlap and the verification can be consolidated.
- `rewrite`: implementation coupling, weak assertions, or excessive mocking dominate.
- `delete`: the test is close to a tautological assertion, liar test, or rechecks deleted behavior.

## Sensitive Smells

- Excessive mocking
- Implementation duplication
- Hallucinated rules
- Flaky timing dependence
- Important behavior hidden inside snapshots
