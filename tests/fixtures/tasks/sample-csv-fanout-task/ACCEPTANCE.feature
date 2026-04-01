Feature: Parallel Workflow Runtime

  Scenario: Parallel runtime artifacts are created for the slice
    Given a slice with `Execution skill: parallel-workflow`
    When the parallel runtime starts
    Then `Documentation.md`, `info-collection.csv`, `implementation.csv`, and `review.csv` exist under `runs/parallel-workflow/SLICE-1/`

  Scenario: Shared-file work falls back to a single lane
    Given an implementation row with `shared_file_touch=Y`
    When the runtime finalizes implementation rows
    Then the row is marked `parallelizable=false` or grouped by `change_group_id`
    And `execution_mode` records the fallback reason
