# Created by marco at 31-10-2015
Feature: Collect data from buienradar
  # Enter feature description here

  Scenario: Collect data from buienradar when available
    Given the system is online
    When we collect data from buienradar
    Then we have the data

  Scenario: Stop collecting when buienradar is not available
    Given the system is online
    And buienradar is not reachable
    When we collect data from buienradar
    Then we have dummy data