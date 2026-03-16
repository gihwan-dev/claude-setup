# ADR-0001: CSV Fan-out Architecture

## Status

Accepted

## Context

Independent API endpoints can be generated in parallel. Sequential execution is unnecessarily slow.

## Decision

Use `csv-fanout` execution topology with row-level worker isolation.

## Consequences

- Faster execution via parallelism.
- Row workers must respect `target_path` isolation.
- Shared file modifications require integrator role.
