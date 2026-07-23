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
    return {"response": response, "ingredients": [first_ingredient, second_ingredient]}


_TRIGGER_TEXT = (
    'a Mealie recipe action is triggered for the recipe "{recipe_name}" '
    'with the ingredients "{first_ingredient}" and "{second_ingredient}"'
)


@given(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
@when(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
def recipe_action_triggered(running_app, recipe_name, first_ingredient, second_ingredient):
    return _trigger_recipe_action(running_app, recipe_name, first_ingredient, second_ingredient)


@then(parsers.parse('I see the shopping lists "{first_list}" and "{second_list}" to choose from'))
def see_shopping_lists(triggered, first_list, second_list):
    body = triggered["response"].get_data(as_text=True)
    assert first_list in body
    assert second_list in body


def _select_shopping_list(running_app, triggered, shopping_lists_by_name, list_name):
    list_id = shopping_lists_by_name[list_name]
    response = running_app.post(
        f"/shopping-lists/{list_id}",
        data=MultiDict(("ingredient", ingredient) for ingredient in triggered["ingredients"]),
    )
    return {"response": response, "list_id": list_id, "ingredients": set(triggered["ingredients"])}


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


@when(parsers.parse('I deselect the ingredient "{ingredient}"'), target_fixture="selection")
def deselect_ingredient(selection, ingredient):
    selection["ingredients"].discard(ingredient)
    return selection


@when("I confirm the ingredient selection", target_fixture="push_response")
def confirm_ingredient_selection(running_app, selection):
    return running_app.post(
        f"/shopping-lists/{selection['list_id']}/confirm",
        data=MultiDict(("ingredient", ingredient) for ingredient in selection["ingredients"]),
    )


def _shopping_list_item_names(kitchenowl_household, shopping_lists_by_name, list_name) -> set[str]:
    list_id = shopping_lists_by_name[list_name]
    items = kitchenowl_household.server.get_shopping_list_items(kitchenowl_household.id, list_id)
    return {item["name"] for item in items}


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
    item_names = _shopping_list_item_names(kitchenowl_household, shopping_lists_by_name, list_name)
    assert item_names == {first_ingredient, second_ingredient}


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
    item_names = _shopping_list_item_names(kitchenowl_household, shopping_lists_by_name, list_name)
    assert item_names == {ingredient}
