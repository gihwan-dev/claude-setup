# Merge Policy

## Integrator-only shared files

The following files may only be modified by the integrator role:

- `index.ts` (barrel exports)
- `routes.ts` (route registration)
- `package.json` (dependency additions)

## Row worker scope

Each row worker may only create or modify files under its assigned `target_path`.
Cross-row file references are forbidden.

## Merge strategy

The integrator collects row outputs and applies shared-file updates in a single pass.

## Conflict handling

If two row outputs affect the same shared file section, the integrator must:
1. Detect the overlap.
2. Apply changes in row_id order.
3. Report any unresolvable conflicts as merge failures.
