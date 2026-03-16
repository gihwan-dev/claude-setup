# Global Context

## Token budget

Each row worker receives a maximum of 8000 tokens for its task context.

## Layout/Import rules

- All generated files must follow the project's existing directory layout.
- Import paths must be relative to the project root.

## Shared-file touch rules

- Row workers must not modify files outside their `target_path`.
- Shared files (`index.ts`, `routes.ts`, barrel exports) are integrator-only.
- GLOBAL_CONTEXT.md itself is read-only for all row workers.
