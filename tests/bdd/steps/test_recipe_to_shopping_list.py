from pytest_bdd import given, parsers, scenarios, then, when
from werkzeug.datastructures import MultiDict

from .common import *  # noqa: F401,F403

scenarios("../features/recipe_to_shopping_list.feature")


@given(
    parsers.parse('KitchenOwl has the shopping lists "{first_list}" and "{second_list}"'),
    target_fixture="shopping_lists_by_name",
)
def kitchenowl_has_shopping_lists(requests_mock, config, first_list, second_list):
    lists = [{"id": 1, "name": first_list}, {"id": 2, "name": second_list}]
    requests_mock.get(
        f"{config.kitchenowl_url}/api/household/{config.kitchenowl_household_id}/shoppinglist",
        json=lists,
    )
    return {item["name"]: item["id"] for item in lists}


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


@when(parsers.parse('I select the shopping list "{list_name}"'), target_fixture="push_response")
def select_shopping_list(
    running_app, triggered, shopping_lists_by_name, list_name, requests_mock, config
):
    list_id = shopping_lists_by_name[list_name]
    requests_mock.post(
        f"{config.kitchenowl_url}/api/household/{config.kitchenowl_household_id}"
        f"/shoppinglist/{list_id}/add-item-by-name",
        json={},
    )
    return running_app.post(
        f"/shopping-lists/{list_id}",
        data=MultiDict(("ingredient", ingredient) for ingredient in triggered["ingredients"]),
    )


@then(
    parsers.parse(
        'the ingredients "{first_ingredient}" and "{second_ingredient}" are added to the '
        '"{list_name}" shopping list in KitchenOwl'
    )
)
def ingredients_added_to_shopping_list(
    push_response,
    requests_mock,
    config,
    shopping_lists_by_name,
    list_name,
    first_ingredient,
    second_ingredient,
):
    assert push_response.status_code == 200

    list_id = shopping_lists_by_name[list_name]
    add_item_path = (
        f"/api/household/{config.kitchenowl_household_id}/shoppinglist/{list_id}/add-item-by-name"
    )
    added_names = {
        request.json()["name"]
        for request in requests_mock.request_history
        if request.method == "POST" and request.path == add_item_path
    }
    assert added_names == {first_ingredient, second_ingredient}
