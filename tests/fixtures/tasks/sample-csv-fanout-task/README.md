# Sample CSV Fan-out Task

## Goal

Demonstrate the split between design-time `csv-fanout` planning and runtime
`parallel-workflow` execution artifacts.

## Document map

- `task.yaml` — machine entry point
- `PRD.md` — product requirements
- `TECH_SPEC.md` — technical specification
- `EXECUTION_PLAN.md` — execution slices
- `SPEC_VALIDATION.md` — validation gate
- `STATUS.md` — progress tracking
- `ACCEPTANCE.feature` — acceptance criteria
- `ADRs/` — architecture decision records
- `runs/parallel-workflow/SLICE-1/` — runtime execution artifacts for the
  parallel slice

## Key decisions

- ADR-0001: keep `csv-fanout` as a planning topology, but move runtime CSVs
  under `parallel-workflow`
- Shared-file work is not independently parallelized; it collapses into a
  change-group single lane

## Validation gate status

blocking — `architecture_significant` flag is set.

## Implementation slice order

SLICE-1: `parallel-workflow` executes the API endpoint slice through
`info-collection.csv`, `implementation.csv`, and `review.csv`.
