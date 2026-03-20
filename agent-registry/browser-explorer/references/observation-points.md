# Browser Explorer Observation Points

## What To Protect

- Reproducibility
- Visual regressions and layout drift
- Awkward interaction flow
- Behavior sensitive to hidden prerequisites

## Evidence Lens

- Prefer observable behavior over code descriptions.
- Record visual evidence and interaction results by separating facts from interpretation.
- Treat failed reproduction as a useful signal and make required preconditions explicit.

## Smells

- Bugs that appear only under narrow conditions
- UI states that disagree with actual behavior
- Broken focus, scroll, or input flow
- Small style regressions that change meaning
