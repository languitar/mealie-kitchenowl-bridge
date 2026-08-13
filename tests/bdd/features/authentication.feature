Feature: Authentication
  As the operator of the bridge
  I want the recipe-action trigger to require a shared secret
  So that only Mealie can trigger the bridge

  Scenario: A recipe action with an invalid trigger token is rejected
    Given the bridge is running
    And the trigger token is invalid
    When a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    Then the request is rejected as unauthorized

  Scenario: A recipe action with a valid trigger token is accepted
    Given the bridge is running
    And the trigger token is valid
    When a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    Then I see the shopping lists to choose from
