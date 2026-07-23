Feature: Push recipe ingredients to a KitchenOwl shopping list
  As a Mealie user
  I want to pick a KitchenOwl shopping list when I trigger a recipe's action
  So that the recipe's ingredients end up on the shopping list I choose

  Background:
    Given the bridge is running
    And KitchenOwl has the shopping lists "Groceries" and "Household"

  Scenario: The selection dialog lists the available shopping lists
    When a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    Then I see the shopping lists "Groceries" and "Household" to choose from

  Scenario: Selecting a shopping list shows the recipe's ingredients, all pre-selected
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    When I select the shopping list "Groceries"
    Then I see the ingredients "Tomatoes" and "Basil", all pre-selected

  Scenario: Confirming the ingredient selection adds all pre-selected ingredients to the shopping list
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    And I have selected the shopping list "Groceries"
    When I confirm the ingredient selection
    Then the ingredients "Tomatoes" and "Basil" are added to the "Groceries" shopping list in KitchenOwl

  Scenario: Deselecting an ingredient excludes it from the shopping list push
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    And I have selected the shopping list "Groceries"
    When I deselect the ingredient "Basil"
    And I confirm the ingredient selection
    Then only the ingredient "Tomatoes" is added to the "Groceries" shopping list in KitchenOwl
