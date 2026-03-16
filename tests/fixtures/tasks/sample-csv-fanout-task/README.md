# Sample CSV Fan-out Task

## Goal

Demonstrate CSV fan-out execution topology for parallel row-level processing.

## Document map

- `task.yaml` — machine entry point
- `PRD.md` — product requirements
- `TECH_SPEC.md` — technical specification
- `EXECUTION_PLAN.md` — execution slices
- `SPEC_VALIDATION.md` — validation gate
- `STATUS.md` — progress tracking
- `ACCEPTANCE.feature` — acceptance criteria
- `ADRs/` — architecture decision records
- `GLOBAL_CONTEXT.md` — shared context for row workers
- `MERGE_POLICY.md` — merge strategy for shared files
- `work-items/` — CSV work item definitions

## Key decisions

- ADR-0001: Use csv-fanout topology for independent API endpoint generation.
- Row workers operate on `target_path` only; shared files are integrator-only.

## Validation gate status

blocking — architecture_significant flag is set.

## Implementation slice order

SLICE-1: CSV fan-out parallel execution of API endpoint stubs.
