# Storybook Screenshot Guidelines

Shared Storybook and screenshot rules used by `design-check` and `story-generator`.

## Scope

- Use this when creating or updating Stories for screenshot comparison.
- The canonical source remains each skill's `SKILL.md`, but the shared Story rules live here.

## Story Placement

- Default location: `__screenshots__/{ComponentName}.stories.tsx` next to the component
- Reuse an existing screenshot Story first when one already exists.
- Confirm before overwriting a file with the same name.

## Title Rules

- Format: `Screenshots/{Layer}/{ComponentName}`
- If there is a nested path, use `Screenshots/{Layer}/{SubPath}/{ComponentName}`
- Use PascalCase for `Layer`.
- Example: `src/features/widget-builder/ui/ColumnHeader.tsx`
  - `Screenshots/Features/WidgetBuilder/ColumnHeader`

## Rendering Rules

- `render` must return a single root element.
- Import paths must use the `@/` alias.
- The wrapper acts as the screenshot container.
- Set width from the Figma bbox or the requested capture width.
- Do not force height unless there is a specific reason. Height differences should remain visible in the actual diff.

## Classification

| Classification | Condition | Default Response |
|------|------|-----------|
| Simple | Only props are needed | Render directly |
| MSW-dependent | API calls, `useQuery`, or similar | Add MSW handlers |
| Provider-dependent | Depends on Context or Store | Wrap with a Provider decorator |

When an existing Story is available, reuse its args, decorators, and parameters patterns as much as possible.

## Capture Contract

- A Story used for Storybook capture must render reliably under the `#storybook-root > *` selector.
- Right after creating a new Story, treat `--rebuild` as the default.
- For Figma-based comparison, wire `bbox.width` into `--container-width`.

## Validation Checklist

- Is the TypeScript syntax valid?
- Does the title follow the `Screenshots/...` rule?
- Do imports use the `@/` alias?
- Does `render` return a single root element?
- Does the wrapper width match the capture goal?
