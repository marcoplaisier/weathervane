Feature: Parse buienradar json
  Use the buienradar json feed

  Scenario: pass correct json
    Given data from buienradar in json format
    When the data is parsed
    Then usable weatherdata is returned