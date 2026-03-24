# Browser Explorer Observation Points

## What To Protect

- Reproducibility
- Visual regressions and layout drift
- Awkward interaction flow
- Behavior sensitive to hidden prerequisites
- Network behavior fidelity -- request/response correctness and timing
- Authentication and session state integrity across navigation
- Cross-viewport consistency (mobile, tablet, desktop)

## Evidence Lens

- Prefer observable behavior over code descriptions.
- Record visual evidence and interaction results by separating facts from interpretation.
- Treat failed reproduction as a useful signal and make required preconditions explicit.
- Use HAR recordings and network traces alongside screenshots when behavior depends on API calls.
- Use page snapshots (accessibility tree) as primary evidence for element state, not just visual appearance.
- Verify issues reproduce in clean sessions, not just in existing browser state.

## Smells

- Bugs that appear only under narrow conditions
- UI states that disagree with actual behavior
- Broken focus, scroll, or input flow
- Small style regressions that change meaning
- Auth state that silently expires or leaks between sessions
- Network requests that fire unexpectedly on navigation or interaction
- Viewport-dependent layout breakage at specific breakpoints
- Element refs that go stale between interactions (uncontrolled DOM mutations)
