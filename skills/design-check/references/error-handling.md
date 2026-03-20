# Design Check Error Handling

## Hard Stop

| Situation | Response |
|------|------|
| Failed to parse `node-id` from the Figma URL | Stop and show a valid URL example |
| Failed to capture the Figma screenshot | Stop instead of continuing without the bbox |
| Component file missing | Ask the user to verify the path, then stop |
| Storybook build or capture fails completely | Leave a reproduction command and stop |

## Continue With Warning

| Situation | Response |
|------|------|
| `get_design_context` fails | Narrow the qualitative analysis scope and continue |
| `get_variable_defs` fails | Mark the Design Tokens section as `Not available` |
| Image size mismatch | Note the mismatch in the report and still generate the diff |

## Common Operator Guidance

- `FIGMA_TOKEN` missing: show how to create the token.
- 403: ask the user to verify file access and token permissions.
- 404: ask the user to verify the `fileKey` or `nodeId`.
- Image URL is null: ask the user to confirm the node is renderable in Figma.
- Empty screenshot or timeout: check the Story URL plus the `--timeout` and `--rebuild` conditions first.
