# Technical Specification: Parallel Runtime Architecture

## Overview

The task bundle keeps only static `csv-fanout` intent. Runtime execution moves
to `implement-task` under `runs/<slice-id>/`.

## Architecture

- `design-task` records static orchestration metadata in `task.yaml`.
- `multi-work` locks helper routing when agent type or shard basis is not yet fixed.
- `implement-task` creates `Documentation.md`, `info-collection.csv`,
  `implementation.csv`, and `review.csv`.
- Shared-file rows are grouped by `change_group_id` and run single-lane.
- `verification-worker` summarizes runtime validation output for the manager lane.

## Constraints

- Parallel execution requires a locked agent type and shard basis.
- `implementation.csv` exists before implementation rows are finalized.
- Advisory review findings stay review-only by default.
