Feature: Trigger the bridge from a real Mealie recipe action
  As a Mealie user
  I want clicking the bridge's recipe action in Mealie to open the bridge
  So that I actually land on the shopping-list-selection screen

  Scenario: Clicking the Link action opens the bridge's shopping list selection
    Given the bridge is running as a logged-in user
    And a real Mealie recipe "Tomato Soup" with the ingredient "Tomatoes"
    And the bridge's recipe action is configured on that recipe in Mealie
    When I open the recipe in Mealie and trigger its action
    Then a new browser tab shows the bridge's shopping list selection for "Tomato Soup"
