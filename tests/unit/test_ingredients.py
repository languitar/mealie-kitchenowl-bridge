from bridge.ingredients import Ingredient, parse_ingredient


def test_uses_food_name_when_present():
    ingredient = parse_ingredient({"display": "2 cups Tomatoes", "food": {"name": "Tomatoes"}})
    assert ingredient.name == "Tomatoes"


def test_falls_back_to_display_without_a_food():
    ingredient = parse_ingredient({"display": "Some fresh herbs"})
    assert ingredient.name == "Some fresh herbs"


def test_no_quantity_field_means_no_quantity():
    ingredient = parse_ingredient({"display": "Basil", "food": {"name": "Basil"}})
    assert ingredient == Ingredient(name="Basil", quantity=None)


def test_quantity_without_unit_has_no_unit_suffix():
    ingredient = parse_ingredient(
        {"display": "2 Tomatoes", "food": {"name": "Tomatoes"}, "quantity": 2}
    )
    assert ingredient.quantity == "2"


def test_quantity_with_unit_is_combined():
    ingredient = parse_ingredient(
        {
            "display": "2 cups Tomatoes",
            "food": {"name": "Tomatoes"},
            "quantity": 2,
            "unit": {"name": "cups"},
        }
    )
    assert ingredient.quantity == "2 cups"


def test_fractional_quantity_is_not_truncated():
    ingredient = parse_ingredient(
        {
            "display": "0.5 cups Tomatoes",
            "food": {"name": "Tomatoes"},
            "quantity": 0.5,
            "unit": {"name": "cups"},
        }
    )
    assert ingredient.quantity == "0.5 cups"
