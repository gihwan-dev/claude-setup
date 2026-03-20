# Token Mapping

Mapping rules used by `figma-to-code` when translating Figma design values into React and Tailwind code.

## Color Mapping Priority

1. If Figma provides a variable binding, use that name directly.
   - Example: `color/gray-05` -> `text-gray-05`
2. Prefer semantic tokens.
   - text: `text-text-primary`, `text-text-secondary`, `text-text-tertiary`, `text-text-disabled`, `text-text-accent`, `text-text-critical`
   - surface: `bg-surface-primary-default`, `bg-elevation-elevation-0`
   - border: `border-border-primary`, `border-border-secondary`
   - icon: `text-icon-primary`, `text-icon-secondary`
3. If no semantic match exists, use the primitive color scale.
   - `gray-00~10`, `red-00~10`, `blue-00~10`, `mono-white`, `mono-black`
4. If an exact match still does not exist, use the nearest token and leave a TODO.

## Typography

| Figma Size | Tailwind Class |
|---|---|
| 28px/140% | `text-header-1` |
| 24px/140% | `text-header-2` |
| 20px/140% | `text-title-1` |
| 18px/140% | `text-title-2` |
| 16px/140% | `text-body-1` |
| 14px/140% | `text-body-2` |
| 12px/140% | `text-body-3` |
| 11px/140% | `text-caption` |

Font weight mapping:

- 400 -> `font-regular`
- 500 -> `font-medium`
- 600 -> `font-semibold`
- 700 -> `font-bold`

## Radius And Shadow

- radius: `rounded-weak`, `rounded-medium`, `rounded-strong`, `rounded-circle`
- shadow: `shadow-weak`, `shadow-medium`, `shadow-strong`, `shadow-preview`

## Layout Mapping

- auto-layout direction -> `flex flex-row` / `flex flex-col`
- gap, padding -> prefer standard spacing; use arbitrary values only when needed
- child sizing
  - fill -> `flex-1`
  - fixed -> `w-[Npx]`
  - hug -> `w-fit`

## Component Recognition

- For Figma component instances, first look for an `@exem-fe/react` mapping.
  - Example: `Button`, `TextField`, `Select`, `Table`, `Tabs`, `Modal`, `Tooltip`, `Badge`, `Tag`, `Checkbox`, `Radio`, `Switch`
- If the project's custom UI is a closer match, prefer similar components in `src/shared/ui/`.
  - Example: `Card`, `Form`, `DropdownMenu`, `Sheet`, `Popover`, `Skeleton`
- For icons, first try the `{Name}{Variant}Icon` pattern from `@exem-fe/icon`.

## Code Generation Defaults

- Import order: external packages -> `@exem-fe/*` -> `@/` -> relative paths
- Use `cn()` from `@/shared/util` for className merging.
- Always leave a `className?: string` composition path on the root element.
- Prefer string props for text nodes and array or `children` props for repeated elements.
- Use named exports instead of default exports.
