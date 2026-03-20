# Error Handling And Output

Common failure cases and the result summary format for `figma-to-code`.

## Overwrite Policy

- If the target file is not empty, confirm overwrite before writing.
- If overwrite is denied, suggest a new file path or stop.

## Error Cases

| Situation | Response |
|---|---|
| URL has no `node-id` | Ask for a valid Figma URL and explain that `node-id` is required |
| MCP call fails | Ask the user to open the Figma Desktop app and the target file |
| Variable or token matching fails | Use the closest token and leave a TODO |
| Target file is not empty | Do not write until overwrite is confirmed |

## Result Summary Format

```text
Figma -> Code complete: {ComponentName}

Design tokens used:
- Colors: {token list}
- Typography: {type list}
- Other: {radius/shadow/etc}

Components used:
- @exem-fe/react: {...}
- @exem-fe/icon: {...}
- @/shared/ui: {...}

Generated file: {component path}
```

## Example Input

```text
/figma-to-code https://figma.com/design/abc123/MyProject?node-id=1-2 src/features/widget-builder/ui/ColumnHeader.tsx
```

## Example Execution Summary

```text
1. Parse inputs: nodeId=`1:2`, component=`ColumnHeader`
2. Collect Figma data: screenshot/context/variables
3. Inspect local patterns: check `src/shared/ui/` and sibling files
4. Map tokens: Figma values -> Tailwind token classes
5. Generate code: `ColumnHeader.tsx`
6. Validate: token usage, import alias, and named exports
```
