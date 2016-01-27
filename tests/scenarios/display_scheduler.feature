# Created by marco at 27-Jan-16
Feature: Turn on or turn off the display at certain times

    Scenario: Turn display on
    Given a display
    And the display is turned off
    When the turn-on time is reached
    Then the display is turned on

  Scenario: Turn display off
    Given a display
    And the display is turned on
    When the turn-off time is reached
    Then the display is turned off