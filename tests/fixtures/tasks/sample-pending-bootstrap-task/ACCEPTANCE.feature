Feature: pending bootstrap timeline task bundle

  Scenario: bootstrap blocker must clear first
    Given greenfield implementation rules are not fixed
    When reviewing the pending bundle
    Then `$bootstrap-project-rules` remains in blocking issues

  Scenario: open overview after bootstrap
    Given bootstrap is completed later
    When opening the overview
    Then a timeline-first list is rendered
