# ADR-0001: CSV Fan-out Runtime Boundary

## Status

Accepted

## Context

Independent API endpoints can still be planned as `csv-fanout`, but runtime CSV
artifacts should not live in the top-level task bundle.

## Decision

Keep `csv-fanout` as a design-time topology and move runtime execution artifacts
to `implement-task` under `runs/<slice-id>/`.

## Consequences

- Design bundles stay stable and planning-focused.
- Runtime CSVs become replaceable execution artifacts.
- Shared-file modifications must collapse to a single lane or change group.
