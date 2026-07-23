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

  Scenario: Selecting a shopping list adds the recipe's ingredients to it
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredients "Tomatoes" and "Basil"
    When I select the shopping list "Groceries"
    Then the ingredients "Tomatoes" and "Basil" are added to the "Groceries" shopping list in KitchenOwl
