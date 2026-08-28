Feature: Authentication
  As the operator of the bridge
  I want every page of the bridge to require signing in via the configured OIDC provider
  So that only authorized users can reach it

  Scenario: An unauthenticated visit to the recipe action trigger is sent to log in
    Given the bridge is running
    When a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients:
      |  | Tomatoes |
      |  | Basil    |
    Then I am redirected to log in

  Scenario: Completing login returns to the originally requested recipe action
    Given the bridge is running
    And a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients:
      |  | Tomatoes |
      |  | Basil    |
    When I complete login with the identity provider
    Then I see the shopping lists to choose from
