# Design Check Workflow Details

This document expands the core flow from `SKILL.md` into concrete stages and commands.

## Stage 1: Parallel Collection

### A. Figma screenshot + bbox metadata

```bash
pnpm exec tsx ${SKILL_DIR}/scripts/capture-figma-screenshot.ts \
  --url "{figmaUrl}" \
  --output "artifacts/screenshots/figma/{Name}.png" \
  --scale 2
```

- Read `bbox.width` and `bbox.height` from `.meta.json`.
- Pipe `bbox.width` into `--container-width` for the implementation capture step.

### B. Figma context + variable definitions

- `get_design_context(nodeId)`
- `get_variable_defs(nodeId)`

Task B may continue with a warning if it fails.

### C. Story preparation

- Analyze component exports, props, and import dependencies.
- The screenshot Story must follow `../_shared/storybook-screenshot-guidelines.md`.
- If a new Story is required, start from `../_shared/storybook-screenshot-template.tsx`.

## Stage 2: Bbox Injection and Implementation Capture

1. Replace the Story wrapper width placeholder with `bbox.width`.
2. Build the Storybook story ID.
3. Capture the implementation screenshot.

```bash
pnpm exec tsx ${SKILLS_ROOT}/component-screenshot/scripts/capture-screenshot.ts \
  --story-id "{storyId}" \
  --output "artifacts/screenshots/impl/{Name}.png" \
  --width {viewportWidth} \
  --height {viewportHeight} \
  --scale 2 \
  --container-width {bboxWidth} \
  --rebuild
```

## Stage 3: Quantitative Comparison

```bash
pnpm exec tsx ${SKILL_DIR}/scripts/compare-screenshots.ts \
  --base "artifacts/screenshots/figma/{Name}.png" \
  --current "artifacts/screenshots/impl/{Name}.png" \
  --output "artifacts/screenshots/diff/{Name}.png"
```

The report must include at least:

- `diffPixels`
- `diffRatio`
- `result`
- Whether a size mismatch occurred

## Stage 4: Qualitative Review

Compare:

- layout / alignment / spacing
- typography
- color
- icon/image size and placement
- responsive/container fit

Use four severity levels: `Critical`, `Major`, `Minor`, and `Nitpick`.

## Report Skeleton

Output path: `artifacts/design-check/{Name}-report.md`

Required sections:

1. Executive Summary
2. Quantitative Analysis
3. Qualitative Analysis
4. Design Tokens
5. Recommendations
6. Artifacts
