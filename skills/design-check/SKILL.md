---
name: design-check
description: >
  Automated design verification comparing Figma designs vs implemented components
  with pixel-diff reports. Requires: component-screenshot skill. Use for "/design-check",
  "run design verification", or Figma vs implementation comparison. Do not use when
  Figma URL is unavailable or Storybook is not configured.
allowed-tools: Bash, Read, Grep, Glob, Agent
---

# Design Check

Compare a Figma design against an implemented component and produce screenshot artifacts plus a Markdown report.

## Trigger

- `/design-check`
- `run design verification`
- When a Figma URL and component path are both available and visual comparison is needed

## Required Inputs

- Figma URL
  - `fileKey` and `node-id` must be extractable
- Implemented component path
- `FIGMA_TOKEN`
- A project environment with Storybook available

## Outputs

- `artifacts/screenshots/figma/{Name}.png`
- `artifacts/screenshots/figma/{Name}.meta.json`
- `artifacts/screenshots/impl/{Name}.png`
- `artifacts/screenshots/diff/{Name}.png`
- `artifacts/design-check/{Name}-report.md`
- `__screenshots__/{ComponentName}.stories.tsx` when needed

## Core Flow

1. Extract `fileKey`, `nodeId`, and the target name from the Figma URL.
2. Capture the Figma screenshot and bbox metadata.
3. Collect design context and token data. This step may continue with a warning.
4. Analyze the component and prepare a screenshot Story.
   - Story rules come from `../_shared/storybook-screenshot-guidelines.md`
   - Use `../_shared/storybook-screenshot-template.tsx` as the shared starting point
5. Inject only `bbox.width` into the Story wrapper and capture options to create the implementation screenshot.
6. Compute the pixel diff and perform the qualitative comparison.
7. Combine the quantitative and qualitative results into a report.

## Guardrails

- Stop if the bbox cannot be retrieved. Do not continue comparison without the width contract.
- If design context or token collection fails, leave a warning and continue with the remaining flow.
- Screenshot Stories must keep a single-root render, the `@/` import alias, and the `Screenshots/...` title rule.
- Match width to the Figma bbox and do not force height unless there is a specific reason.
- Confirm before overwriting an existing screenshot Story or artifact.
- The report must include at least the diff ratio, findings grouped by severity, and artifact paths.

## References

- Detailed steps and commands: `references/workflow-details.md`
- Error handling: `references/error-handling.md`
- Shared Storybook and screenshot rules: `../_shared/storybook-screenshot-guidelines.md`
- Shared Story template: `../_shared/storybook-screenshot-template.tsx`
- Related scripts:
  - `scripts/capture-figma-screenshot.ts`
  - `scripts/compare-screenshots.ts`
