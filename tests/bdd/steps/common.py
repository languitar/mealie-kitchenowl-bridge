"""Step definitions shared across multiple .feature files.

Add new capability-specific steps to a dedicated module next to the
feature they belong to; only promote a step here once a second feature
needs it verbatim.
"""

from flask.sessions import SecureCookieSessionInterface
from pytest_bdd import given, parsers, when

_LOGGED_IN_USER = {"sub": "test-user", "email": "test-user@example.com"}


@given("the bridge is running")
def bridge_is_running(live_server):
    pass


def log_in_browser_context(context, app, live_server):
    """Inject a signed Flask session cookie so a browser context starts already
    logged in.

    Playwright can't drive a real OIDC redirect dance through a third-party
    identity provider, so this bypasses login by minting the same signed
    cookie Flask's own login flow would produce.
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


@given("the bridge is running as a logged-in user")
def bridge_is_running_as_logged_in_user(context, app, live_server):
    log_in_browser_context(context, app, live_server)


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


def _split_quantity(quantity: str) -> tuple[float, str | None]:
    amount, _, unit_name = quantity.partition(" ")
    return float(amount), unit_name or None


def build_ingredient(quantity: str, name: str) -> dict:
    """Build a `recipeIngredient` dict for `stub_recipe`, as parsed from one row of a
    trigger step's data table (an empty `quantity` cell means no quantity).
    """
    if not quantity:
        return {"display": name, "food": {"name": name}}
    amount, unit_name = _split_quantity(quantity)
    return {
        "display": f"{quantity} {name}",
        "food": {"name": name},
        "quantity": amount,
        "unit": {"name": unit_name} if unit_name else None,
    }


_TRIGGER_TEXT = (
    'a Mealie recipe action is triggered for the recipe "{recipe_name}" '
    "with the ingredients:"
)


@given(parsers.parse(_TRIGGER_TEXT))
@when(parsers.parse(_TRIGGER_TEXT))
def recipe_action_triggered(page, live_server, requests_mock, config, recipe_name, datatable):
    recipe_ingredients = [build_ingredient(quantity, name) for quantity, name in datatable]
    slug = slugify(recipe_name)
    stub_recipe(requests_mock, config, slug, recipe_name, recipe_ingredients)
    page.goto(f"{live_server.url('/recipes/action')}?slug={slug}")
