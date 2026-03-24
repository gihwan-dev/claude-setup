---
name: figma-to-code
description: >
  Generate React component code from a Figma URL and target file path. Collects
  design data, reads local project patterns and token rules, and produces React code.
  Use for single-component Figma-to-code conversion. Do not use for page-level work
  (use figma-codex-pipeline instead) or when no Figma URL is provided.
allowed-tools: Read, Grep, Glob, Write
---

# Figma to Code

Read Figma design data and generate React component code that follows local project patterns and token rules.

## Trigger

- `/figma-to-code`
- `implement this Figma`
- Requests that include both a Figma URL and a target component file path

## Required Inputs

- Figma URL including `node-id`
- Target component file path
- Whether overwrite is allowed when the target file is not empty

## Core Flow

1. Extract `fileKey` and `nodeId` from the Figma URL. If the URL uses `.../branch/:branchKey/...`, normalize `branchKey` into `fileKey`. Also derive the component name and local context from the target file path.
2. Collect design data by calling `get_screenshot`, `get_design_context`, and `get_variable_defs` in parallel with the `clientLanguages=typescript` and `clientFrameworks=react` hints.
3. Read the target directory and similar components to understand local patterns such as `cn()`, exports, props, and aliases.
4. Decide token, typography, layout, and component mapping using `references/token-mapping.md`.
5. Generate React code that prefers `@exem-fe/react`, follows the `@/` alias, uses named exports, and keeps root `className` composition intact.
6. Summarize the result using the output contract in `references/error-handling.md`, then validate the generated output against the target conventions.

## Guardrails

- Stop if the URL has no `node-id`, and ask for a correct Figma URL.
- If Figma data collection fails, ask the user to open the Figma Desktop app and the target file.
- Never overwrite a non-empty target file without explicit overwrite confirmation.
- Use token-based Tailwind classes instead of hardcoded hex colors.
- Prefer `@exem-fe/react` components over raw HTML when possible.
- Wire a `className` prop into the root element and avoid default exports.

## References

- Token mapping, typography table, radius/shadow rules, and component recognition: `references/token-mapping.md`
- Overwrite policy, URL and MCP error handling, result summary format, and example input/output: `references/error-handling.md`

## Validation

- Confirm that only token-based Tailwind classes are used.
- Confirm that import paths follow the `@/` alias convention.
- Confirm that `cn()` remains in place wherever class merging is required.
- Confirm named exports and sensible component reuse.
