# Created by mplaisier at 14/10/2017
Feature: Parse Buienradar XML into a usable object
  Buienradar provides XML that may or may not be complete. Some values need to be calculated.

  Scenario: complete and simple XML for a single station
    Given Buienradar XML data for a single station
    When the parser parses the data
    Then usable weatherdata is returned

  Scenario: use a fallback when a measurement is missing
    Given Buienradar XML data for two stations where some measurements are missing from the primary station
    When the parser parses the data
    Then usable weatherdata is returned where the missing measurement is supplier by the fallback station