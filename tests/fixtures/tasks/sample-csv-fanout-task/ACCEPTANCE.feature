Feature: CSV Fan-out Execution

  Scenario: Parallel row execution
    Given a work-items CSV with 4 rows
    When csv-fanout execution runs with max_concurrency 4
    Then all 4 row outputs match the output schema
    And the integrator merges shared files without conflict

  Scenario: Row failure recovery
    Given a work-items CSV with 4 rows
    When 1 row worker fails
    Then the failed row is retried once
    And the overall execution succeeds if retry passes
