# Technical Specification: CSV Fan-out Architecture

## Overview

Row-level parallel execution using Codex `spawn_agents_on_csv` pattern.

## Architecture

- Decomposer (main-thread) splits work into CSV rows.
- Row workers execute independently on `target_path`.
- Integrator (`codex-row-worker`) merges shared files per `MERGE_POLICY.md`.
- `verification-worker` summarizes row-validation output after schema checks complete.

## Constraints

- Max concurrency: 4 row workers.
- Row workers must not modify shared files.
- GLOBAL_CONTEXT.md provides token budget and layout rules.
