"""Step definitions shared across multiple .feature files.

Add new capability-specific steps to a dedicated module next to the
feature they belong to; only promote a step here once a second feature
needs it verbatim.
"""

import pytest
from pytest_bdd import given, parsers, when


@given("the bridge is running", target_fixture="running_app")
def bridge_is_running(client):
    return client


@pytest.fixture
def webhook_token(config):
    return config.webhook_token


def slugify(recipe_name: str) -> str:
    """A good-enough slug for stubbing a recipe's fetch URL in tests - not Mealie's real algo."""
    return recipe_name.lower().replace(" ", "-")


def stub_recipe(
    requests_mock, config, slug: str, recipe_name: str, recipe_ingredients: list[dict]
):
    """Stub the Mealie recipe fetch, letting other requests (e.g. to a real KitchenOwl
    container in BDD scenarios that need one) pass through untouched.
    """
    requests_mock.real_http = True
    requests_mock.get(
        f"{config.mealie_url}/api/recipes/{slug}",
        json={"name": recipe_name, "recipeIngredient": recipe_ingredients},
    )


def _trigger_recipe_action(
    running_app,
    webhook_token,
    requests_mock,
    config,
    recipe_name,
    first_ingredient,
    second_ingredient,
):
    slug = slugify(recipe_name)
    stub_recipe(
        requests_mock,
        config,
        slug,
        recipe_name,
        [{"display": first_ingredient}, {"display": second_ingredient}],
    )
    response = running_app.get(
        "/recipes/action",
        query_string={"token": webhook_token, "slug": slug},
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
def recipe_action_triggered(
    running_app,
    webhook_token,
    requests_mock,
    config,
    recipe_name,
    first_ingredient,
    second_ingredient,
):
    return _trigger_recipe_action(
        running_app,
        webhook_token,
        requests_mock,
        config,
        recipe_name,
        first_ingredient,
        second_ingredient,
    )
