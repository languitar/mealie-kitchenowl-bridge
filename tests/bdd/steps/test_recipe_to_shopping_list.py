import re

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from werkzeug.datastructures import MultiDict

from bridge.config import Config

from .common import *  # noqa: F401,F403

scenarios("../features/recipe_to_shopping_list.feature")


@pytest.fixture
def config(config, kitchenowl_household):
    """Point KitchenOwl connection details at the real per-test household.

    Overrides `tests/conftest.py`'s `config` fixture, re-requesting it by the
    same name to keep the (unused, fake) Mealie values as-is - see
    AGENTS.md's BDD workflow notes on testing against a real KitchenOwl.
    """
    return Config(
        mealie_url=config.mealie_url,
        mealie_api_token=config.mealie_api_token,
        kitchenowl_url=kitchenowl_household.server.base_url,
        kitchenowl_api_token=kitchenowl_household.server.admin_token,
        kitchenowl_household_id=str(kitchenowl_household.id),
    )


@given(
    parsers.parse('KitchenOwl has the shopping lists "{first_list}" and "{second_list}"'),
    target_fixture="shopping_lists_by_name",
)
def kitchenowl_has_shopping_lists(kitchenowl_household, first_list, second_list):
    server = kitchenowl_household.server
    return {
        first_list: server.create_shopping_list(kitchenowl_household.id, first_list),
        second_list: server.create_shopping_list(kitchenowl_household.id, second_list),
    }


@given(
    parsers.parse(
        'the shopping list "{list_name}" already has the item "{item_name}" '
        'with quantity "{quantity}"'
    )
)
def shopping_list_already_has_item(
    kitchenowl_household, shopping_lists_by_name, list_name, item_name, quantity
):
    list_id = shopping_lists_by_name[list_name]
    kitchenowl_household.server.add_shopping_list_item(list_id, item_name, quantity)


@pytest.fixture
def kitchenowl_items_by_name() -> dict:
    return {}


@given(
    parsers.parse('KitchenOwl already has an item called "{item_name}"'),
    target_fixture="kitchenowl_items_by_name",
)
def kitchenowl_has_item(kitchenowl_household, kitchenowl_items_by_name, item_name):
    kitchenowl_items_by_name[item_name] = kitchenowl_household.server.create_item(
        kitchenowl_household.id, item_name
    )
    return kitchenowl_items_by_name


@given(parsers.parse('KitchenOwl has no item called "{item_name}"'))
def kitchenowl_has_no_item(kitchenowl_household, item_name):
    items = kitchenowl_household.server.get_items(kitchenowl_household.id)
    assert not any(item["name"].casefold() == item_name.casefold() for item in items)


def _trigger_recipe_action(running_app, recipe_name, first_ingredient, second_ingredient):
    response = running_app.post(
        "/recipes/action",
        json={
            "name": recipe_name,
            "recipeIngredient": [
                {"display": first_ingredient},
                {"display": second_ingredient},
            ],
        },
    )
    return {
        "response": response,
        "ingredients": [
            {"name": first_ingredient, "quantity": None},
            {"name": second_ingredient, "quantity": None},
        ],
    }


_TRIGGER_TEXT = (
    'a Mealie recipe action is triggered for the recipe "{recipe_name}" '
    'with the ingredients "{first_ingredient}" and "{second_ingredient}"'
)


@given(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
@when(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
def recipe_action_triggered(running_app, recipe_name, first_ingredient, second_ingredient):
    return _trigger_recipe_action(running_app, recipe_name, first_ingredient, second_ingredient)


def _split_quantity(quantity: str) -> tuple[float, str | None]:
    amount, _, unit_name = quantity.partition(" ")
    return float(amount), unit_name or None


@given(
    parsers.parse(
        'a Mealie recipe action is triggered for the recipe "{recipe_name}" '
        'with the ingredient "{ingredient_name}" and quantity "{quantity}"'
    ),
    target_fixture="triggered",
)
def recipe_action_triggered_with_quantity(running_app, recipe_name, ingredient_name, quantity):
    amount, unit_name = _split_quantity(quantity)
    response = running_app.post(
        "/recipes/action",
        json={
            "name": recipe_name,
            "recipeIngredient": [
                {
                    "display": f"{quantity} {ingredient_name}",
                    "food": {"name": ingredient_name},
                    "quantity": amount,
                    "unit": {"name": unit_name} if unit_name else None,
                }
            ],
        },
    )
    return {"response": response, "ingredients": [{"name": ingredient_name, "quantity": quantity}]}


@given(
    parsers.parse(
        'a Mealie recipe action is triggered for the recipe "{recipe_name}" '
        'with the ingredient "{ingredient_name}" and no quantity'
    ),
    target_fixture="triggered",
)
def recipe_action_triggered_without_quantity(running_app, recipe_name, ingredient_name):
    response = running_app.post(
        "/recipes/action",
        json={
            "name": recipe_name,
            "recipeIngredient": [
                {"display": ingredient_name, "food": {"name": ingredient_name}},
            ],
        },
    )
    return {"response": response, "ingredients": [{"name": ingredient_name, "quantity": None}]}


@then(parsers.parse('I see the shopping lists "{first_list}" and "{second_list}" to choose from'))
def see_shopping_lists(triggered, first_list, second_list):
    body = triggered["response"].get_data(as_text=True)
    assert first_list in body
    assert second_list in body


def _ingredients_form_data(ingredients) -> MultiDict:
    """Build the same `ingredient`/`quantity:<name>` fields the templates emit.

    Quantity travels in its own per-name field rather than a same-order
    parallel list, so it survives an ingredient being left out (deselected)
    without desynchronizing name/quantity pairs - see `_ingredients_from_form`
    in `bridge/routes/review.py`.
    """
    data = MultiDict()
    for ingredient in ingredients:
        data.add("ingredient", ingredient["name"])
        data.add(f"quantity:{ingredient['name']}", ingredient["quantity"] or "")
    return data


def _selected_item_choice(body: str, ingredient_name: str) -> str:
    """Read the pre-selected `item_choice:<name>` option out of the rendered review screen."""
    select_match = re.search(
        rf'<select name="item_choice:{re.escape(ingredient_name)}">(.*?)</select>', body, re.DOTALL
    )
    assert select_match, f"no item_choice select rendered for {ingredient_name!r}"
    option_match = re.search(r'value="([^"]*)"\s*selected', select_match.group(1))
    assert option_match, f"no selected option rendered for {ingredient_name!r}"
    return option_match.group(1)


def _select_shopping_list(running_app, triggered, shopping_lists_by_name, list_name):
    list_id = shopping_lists_by_name[list_name]
    response = running_app.post(
        f"/shopping-lists/{list_id}",
        data=_ingredients_form_data(triggered["ingredients"]),
    )
    body = response.get_data(as_text=True)
    ingredients = {i["name"]: i["quantity"] for i in triggered["ingredients"]}
    item_choices = {name: _selected_item_choice(body, name) for name in ingredients}
    return {
        "response": response,
        "list_id": list_id,
        "ingredients": ingredients,
        "item_choices": item_choices,
    }


@given(parsers.parse('I have selected the shopping list "{list_name}"'), target_fixture="selection")
@when(parsers.parse('I select the shopping list "{list_name}"'), target_fixture="selection")
def select_shopping_list(running_app, triggered, shopping_lists_by_name, list_name):
    return _select_shopping_list(running_app, triggered, shopping_lists_by_name, list_name)


@then(
    parsers.parse(
        'I see the ingredients "{first_ingredient}" and "{second_ingredient}", all pre-selected'
    )
)
def see_ingredients_pre_selected(selection, first_ingredient, second_ingredient):
    body = selection["response"].get_data(as_text=True)
    for ingredient in (first_ingredient, second_ingredient):
        assert f'value="{ingredient}" checked' in body


@then(
    parsers.parse(
        'I see the ingredient "{ingredient}" matched to the existing KitchenOwl item "{item_name}"'
    )
)
def see_ingredient_matched(selection, kitchenowl_items_by_name, ingredient, item_name):
    body = selection["response"].get_data(as_text=True)
    assert _selected_item_choice(body, ingredient) == str(kitchenowl_items_by_name[item_name])


@then(parsers.parse('I see the ingredient "{ingredient}" set to create a new KitchenOwl item'))
def see_ingredient_set_to_create_new(selection, ingredient):
    body = selection["response"].get_data(as_text=True)
    assert _selected_item_choice(body, ingredient) == "new"


@when(parsers.parse('I deselect the ingredient "{ingredient}"'), target_fixture="selection")
def deselect_ingredient(selection, ingredient):
    selection["ingredients"].pop(ingredient, None)
    return selection


@when(
    parsers.parse(
        'I select the existing KitchenOwl item "{item_name}" for the ingredient '
        '"{ingredient_name}"'
    ),
    target_fixture="selection",
)
def select_existing_item_for_ingredient(
    selection, kitchenowl_items_by_name, item_name, ingredient_name
):
    selection["item_choices"][ingredient_name] = str(kitchenowl_items_by_name[item_name])
    return selection


@when(
    parsers.parse(
        'I choose to create a new KitchenOwl item for the ingredient "{ingredient_name}"'
    ),
    target_fixture="selection",
)
def choose_new_item_for_ingredient(selection, ingredient_name):
    selection["item_choices"][ingredient_name] = "new"
    return selection


@when("I confirm the ingredient selection", target_fixture="push_response")
def confirm_ingredient_selection(running_app, selection):
    ingredients = [
        {"name": name, "quantity": quantity} for name, quantity in selection["ingredients"].items()
    ]
    data = _ingredients_form_data(ingredients)
    for name in selection["ingredients"]:
        data.add(f"item_choice:{name}", selection["item_choices"].get(name, "new"))
    return running_app.post(
        f"/shopping-lists/{selection['list_id']}/confirm",
        data=data,
    )


def _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name) -> dict:
    list_id = shopping_lists_by_name[list_name]
    items = kitchenowl_household.server.get_shopping_list_items(kitchenowl_household.id, list_id)
    return {item["name"]: item for item in items}


@then(
    parsers.parse(
        'the ingredients "{first_ingredient}" and "{second_ingredient}" are added to the '
        '"{list_name}" shopping list in KitchenOwl'
    )
)
def ingredients_added_to_shopping_list(
    push_response,
    kitchenowl_household,
    shopping_lists_by_name,
    list_name,
    first_ingredient,
    second_ingredient,
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items.keys() == {first_ingredient, second_ingredient}


@then(
    parsers.parse(
        'only the ingredient "{ingredient}" is added to the "{list_name}" shopping list '
        "in KitchenOwl"
    )
)
def only_ingredient_added_to_shopping_list(
    push_response, kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items.keys() == {ingredient}


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        'with the description "{description}"'
    )
)
def ingredient_added_with_description(
    push_response, kitchenowl_household, shopping_lists_by_name, list_name, ingredient, description
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items[ingredient]["description"] == description


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        "with no description"
    )
)
def ingredient_added_without_description(
    push_response, kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert not items[ingredient].get("description")


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        'as the existing item "{item_name}"'
    )
)
def ingredient_added_as_existing_item(
    push_response,
    kitchenowl_household,
    shopping_lists_by_name,
    kitchenowl_items_by_name,
    list_name,
    ingredient,
    item_name,
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert ingredient not in items
    assert items[item_name]["id"] == kitchenowl_items_by_name[item_name]


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        "as a new item"
    )
)
def ingredient_added_as_new_item(
    push_response, kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    assert push_response.status_code == 200
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert ingredient in items
