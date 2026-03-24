---
name: story-generator
description: >
  Auto-generate Storybook story files for component screenshot comparison. Use for
  "/story-gen", "generate a Story", or when Story files are needed before screenshot
  capture. Do not use when Story files already exist or Storybook is not configured.
allowed-tools: Read, Grep, Glob, Write
---

# Story Generator

Quickly generate a Storybook Story for screenshot capture and design comparison.

## Trigger

- `/story-gen`
- `generate a Story`
- When a screenshot comparison Story does not exist yet, or when an existing Story needs a screenshot-only variant

## Required Input

- Component file path
- Optional target width or a reference Story to reuse

## Core Flow

1. Extract the component name, layer, and import path from the component path.
2. Read exports, props, and dependencies to classify rendering requirements.
3. Reuse args, decorators, and parameters from an existing Story whenever possible.
4. Create the screenshot Story at `__screenshots__/{ComponentName}.stories.tsx`.
5. Validate the title, render root, import alias, and wrapper width.

## Guardrails

- Follow the Story rules in `../_shared/storybook-screenshot-guidelines.md`.
- Start from `../_shared/storybook-screenshot-template.tsx`.
- Keep the title in `Screenshots/{Layer}/{ComponentName}` format.
- `render` must return a single root element.
- Imports must use the `@/` alias.
- Set width for capture needs; do not force height unless there is a specific reason.
- If a screenshot Story already exists, confirm before overwriting it.

## Classification

| Classification | Condition | Default Response |
|------|------|-----------|
| Simple | Only props are needed | Render directly |
| MSW-dependent | API calls, `useQuery`, or similar | Add MSW handlers |
| Provider-dependent | Depends on Context or Store | Wrap with a Provider decorator |

## References

- Shared Storybook and screenshot rules: `../_shared/storybook-screenshot-guidelines.md`
- Shared Story template: `../_shared/storybook-screenshot-template.tsx`
