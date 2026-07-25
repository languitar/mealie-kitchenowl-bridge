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

  Scenario: Confirming an ingredient with a quantity carries the quantity into KitchenOwl's item description
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredient "Tomatoes" and quantity "2 cups"
    And I have selected the shopping list "Groceries"
    When I confirm the ingredient selection
    Then the ingredient "Tomatoes" is added to the "Groceries" shopping list in KitchenOwl with the description "2 cups"

  Scenario: Confirming an ingredient without a quantity leaves KitchenOwl's item description empty
    Given a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredient "Basil" and no quantity
    And I have selected the shopping list "Groceries"
    When I confirm the ingredient selection
    Then the ingredient "Basil" is added to the "Groceries" shopping list in KitchenOwl with no description

  Scenario: Confirming an ingredient whose quantity unit matches a pre-existing item merges the quantities
    Given the shopping list "Groceries" already has the item "Tomatoes" with quantity "100 g"
    And a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredient "Tomatoes" and quantity "50 g"
    And I have selected the shopping list "Groceries"
    When I confirm the ingredient selection
    Then the ingredient "Tomatoes" is added to the "Groceries" shopping list in KitchenOwl with the description "150g"

  Scenario: Confirming an ingredient whose quantity unit doesn't match a pre-existing item appends a second quantity to its description
    Given the shopping list "Groceries" already has the item "Basil" with quantity "1 cup"
    And a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredient "Basil" and quantity "500 g"
    And I have selected the shopping list "Groceries"
    When I confirm the ingredient selection
    Then the ingredient "Basil" is added to the "Groceries" shopping list in KitchenOwl with the description "1 cup, 500g"

  Scenario: Selecting a shopping list pre-selects a similarly-named existing KitchenOwl item as the match for an ingredient
    Given KitchenOwl already has an item called "Banana"
    And a Mealie recipe action is triggered for the recipe "Fruit Salad" with the ingredient "Bananas" and no quantity
    When I select the shopping list "Groceries"
    Then I see the ingredient "Bananas" matched to the existing KitchenOwl item "Banana"

  Scenario: Selecting a shopping list defaults to creating a new item for an ingredient with no similarly-named match
    Given KitchenOwl has no item called "Tomatoes"
    And a Mealie recipe action is triggered for the recipe "Tomato Soup" with the ingredient "Tomatoes" and no quantity
    When I select the shopping list "Groceries"
    Then I see the ingredient "Tomatoes" set to create a new KitchenOwl item

  Scenario: Changing the matched KitchenOwl item for an ingredient pushes it as that item instead
    Given KitchenOwl already has an item called "Banana"
    And KitchenOwl already has an item called "Plantain"
    And a Mealie recipe action is triggered for the recipe "Fruit Salad" with the ingredient "Bananas" and no quantity
    And I have selected the shopping list "Groceries"
    When I select the existing KitchenOwl item "Plantain" for the ingredient "Bananas"
    And I confirm the ingredient selection
    Then the ingredient "Bananas" is added to the "Groceries" shopping list in KitchenOwl as the existing item "Plantain"

  Scenario: Overriding a matched ingredient to create a new item instead pushes it as a new item
    Given KitchenOwl already has an item called "Banana"
    And a Mealie recipe action is triggered for the recipe "Fruit Salad" with the ingredient "Bananas" and no quantity
    And I have selected the shopping list "Groceries"
    When I choose to create a new KitchenOwl item for the ingredient "Bananas"
    And I confirm the ingredient selection
    Then the ingredient "Bananas" is added to the "Groceries" shopping list in KitchenOwl as a new item
