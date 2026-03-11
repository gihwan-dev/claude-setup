Feature: timeline task bundle

  Scenario: open overview
    Given indexed session events exist
    When opening the overview
    Then a timeline-first list is rendered

  Scenario: drill into thread detail
    Given a thread has wait and tool spans
    When opening thread detail
    Then the related spans are rendered in separate lanes
