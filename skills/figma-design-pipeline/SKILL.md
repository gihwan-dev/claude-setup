---
name: figma-design-pipeline
description: >
  End-to-end Figma-to-code pipeline: converts Figma design to React code then verifies against the original design. Requires: figma-to-code, design-check skills.
  Use when you want a full Figma implementation and verification pipeline that
  runs figma-to-code first and then design-check, such as "/figma-pipeline".
---


# Figma Design Pipeline

This skill is an end-to-end pipeline that implements a Figma design in code and then verifies it against the original design.
It runs `figma-to-code` and then `design-check`.

## Workflow (3 Steps)

### Step 1. Parse Inputs and Run Preflight Checks

Parse the Figma URL and component file path from the user request.

**Parsing:**

1. Extract the `node-id=(\d+-\d+)` pattern from the URL
2. Replace `-` with `:` to build the `nodeId` used for MCP calls
3. Derive the component name and FSD layer from the file path

**Preflight checks:**

- Confirm that the `FIGMA_TOKEN` environment variable exists. `design-check` needs it for Figma REST API screenshot capture in Phase 2.
- If it is missing, stop and explain how to create one: https://www.figma.com/developers/api#access-tokens

### Step 2. Run figma-to-code

Read `${SKILLS_ROOT}/figma-to-code/SKILL.md` and run its full workflow.

Pass the same Figma URL and component path as inputs.

**Completion gate:**
- Confirm that the target file exists
- Confirm that the file contents are not empty
- If either gate fails, tell the user and stop

### Step 3. Run design-check

Read `${SKILLS_ROOT}/design-check/SKILL.md` and run its full workflow.

Pass the same Figma URL and component path to perform design verification.

### Final Output and Iterative Improvement

Combine the results of both steps and output:

```text
Figma Design Pipeline complete: {ComponentName}

[Step 2] figma-to-code result:
- Generated file: {component path}
- Tokens used: {summary of colors, typography, etc.}
- Components used: {list}

[Step 3] design-check result:
- Quantitative: {diffRatio}% ({pass/fail})
- Qualitative: {Critical} Critical, {Major} Major, {Minor} Minor
- Report: {report path}
```

**Iterative improvement:**

If `design-check` finds a **Critical** or **Major** issue:

1. Propose a code change based on the issue
2. If the user approves, apply the code change
3. Re-run only `design-check` to confirm the improvement
4. Repeat until the issue is resolved, up to 3 rounds

## Error Handling

| Situation | Response |
|------|------|
| `FIGMA_TOKEN` missing | Explain how to create a token: https://www.figma.com/developers/api#access-tokens |
| Invalid Figma URL format | Show a valid URL example |
| `figma-to-code` fails | Surface the error and do not run `design-check` |
| `design-check` fails | Surface the error and show partial results when possible |

## Example

### Input

```text
/figma-pipeline https://figma.com/design/abc123/MyProject?node-id=1-2 src/features/widget-builder/ui/ColumnHeader.tsx
```

### Execution

1. **Preflight**: confirmed that `FIGMA_TOKEN` is set
2. **figma-to-code**: collected Figma data -> mapped tokens -> generated `ColumnHeader.tsx`
3. **design-check**: captured screenshots -> compared them -> generated the report

### Output

```text
Figma Design Pipeline complete: ColumnHeader

[Step 2] figma-to-code result:
- Generated file: src/features/widget-builder/ui/ColumnHeader.tsx
- Tokens used: text-text-primary, bg-surface-primary-default, rounded-strong
- Components used: @exem-fe/react (Button), @exem-fe/icon (FilterIcon)

[Step 3] design-check result:
- Quantitative: 1.8% (PASS)
- Qualitative: 0 Critical, 0 Major, 1 Minor
- Report: artifacts/design-check/ColumnHeader-report.md
```
