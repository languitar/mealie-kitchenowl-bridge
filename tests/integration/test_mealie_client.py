import pytest
import requests

from bridge.clients.mealie import MealieClient


@pytest.fixture
def client() -> MealieClient:
    return MealieClient("http://mealie.test", "mealie-token")


def test_get_recipe_returns_the_recipe_body(requests_mock, client):
    requests_mock.get(
        "http://mealie.test/api/recipes/tomato-soup",
        json={"name": "Tomato Soup", "recipeIngredient": [{"display": "Tomatoes"}]},
    )

    recipe = client.get_recipe("tomato-soup")

    assert recipe == {"name": "Tomato Soup", "recipeIngredient": [{"display": "Tomatoes"}]}
    assert requests_mock.last_request.headers["Authorization"] == "Bearer mealie-token"


def test_get_recipe_raises_on_error_response(requests_mock, client):
    requests_mock.get("http://mealie.test/api/recipes/tomato-soup", status_code=404)

    with pytest.raises(requests.HTTPError):
        client.get_recipe("tomato-soup")
