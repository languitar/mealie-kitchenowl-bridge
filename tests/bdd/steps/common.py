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


def _trigger_recipe_action(
    running_app, webhook_token, recipe_name, first_ingredient, second_ingredient
):
    response = running_app.post(
        "/recipes/action",
        query_string={"token": webhook_token},
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
def recipe_action_triggered(
    running_app, webhook_token, recipe_name, first_ingredient, second_ingredient
):
    return _trigger_recipe_action(
        running_app, webhook_token, recipe_name, first_ingredient, second_ingredient
    )
