# Official Patterns

Read this file only when `figma-less-ui-design` needs to lock in product UI direction.

## Reuse + Delta First

- If an existing design system, shipped screen, brand guide, or Figma exists, prefer `reuse + delta` instead of net-new style invention.
- `reuse`: shell, token, primitive, spacing, motion, and copy tone that should be followed as-is
- `delta`: screens, interactions, accessibility or live rules, and degradation policy added or changed for this MVP or prototype

## Reference Pack Rules

- `adopt`: keep only patterns with high product fit that are ready to implement.
- `avoid`: keep patterns that introduce complexity, brand mismatch, or weaker information scent.
- Use references as evidence for shell, hierarchy, live behavior, state handling, and accessibility, not as a moodboard.
- Link saved references directly in the documents with their `DESIGN_REFERENCES/manifest.json` paths.

## App-shell Priorities

- In MVP or prototype work, orientation matters more than novelty.
- The first screen should make navigation, primary work area, and detail context legible at a glance.
- The shell contract should be concrete enough to implement in `SLICE-1`.
- Lock `30-Second Understanding Checklist` and `Glossary + Object Model` before the shell contract.

## Token + Primitive Bias

- Keep tokens minimal and primitive sources explicit.
- Define sources for typography, spacing, surfaces, borders, and status colors first.
- Limit primitive sources to one of: design system, component library, or custom layer.

## Behavior + Accessibility Minimum

- Specify selection sync, drawer or overlay behavior, filter persistence, and keyboard focus order.
- Specify non-color distinction, focus ring, target size, reduced motion, and hover or focus parity.
- Lock live update, stale or reconnect behavior, partial failure, and large-run degradation as separate contracts, not as vague visual direction.
