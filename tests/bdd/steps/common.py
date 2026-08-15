"""Step definitions shared across multiple .feature files.

Add new capability-specific steps to a dedicated module next to the
feature they belong to; only promote a step here once a second feature
needs it verbatim.
"""

from flask.sessions import SecureCookieSessionInterface
from pytest_bdd import given, parsers, when

_LOGGED_IN_USER = {"sub": "test-user", "email": "test-user@example.com"}


@given("the bridge is running", target_fixture="running_app")
def bridge_is_running(client):
    return client


@given("the bridge is running as a logged-in user", target_fixture="running_app")
def bridge_is_running_as_logged_in_user(client):
    with client.session_transaction() as flask_session:
        flask_session["user"] = _LOGGED_IN_USER
    return client


def log_in_browser_context(context, app, live_server):
    """Inject a signed Flask session cookie so a browser-driven (`@browser`)
    scenario starts already logged in.

    Playwright can't drive a real OIDC redirect dance through a third-party
    identity provider, so this bypasses login the same way
    `session_transaction()` does for the Flask-test-client tier - by minting
    the same signed cookie Flask's own login flow would produce.
    """
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    cookie_value = serializer.dumps({"user": _LOGGED_IN_USER})
    context.add_cookies(
        [
            {
                "name": app.config["SESSION_COOKIE_NAME"],
                "value": cookie_value,
                "url": live_server.url("/"),
            }
        ]
    )


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
        query_string={"slug": slug},
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
    requests_mock,
    config,
    recipe_name,
    first_ingredient,
    second_ingredient,
):
    return _trigger_recipe_action(
        running_app,
        requests_mock,
        config,
        recipe_name,
        first_ingredient,
        second_ingredient,
    )
