from dataclasses import replace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from .common import *  # noqa: F401,F403
from .common import _TRIGGER_TEXT, build_ingredient, slugify, stub_recipe

scenarios("../features/authentication.feature")


@pytest.fixture
def config(kitchenowl_config, oidc_server):
    return replace(
        kitchenowl_config,
        oidc_issuer=oidc_server.issuer_url,
        oidc_client_id="bridge-tests-client",
        oidc_client_secret="bridge-tests-secret",  # noqa: S106
    )


@given(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
@when(parsers.parse(_TRIGGER_TEXT), target_fixture="triggered")
def recipe_action_triggered(live_server, requests_mock, config, recipe_name, datatable):
    """Overrides `common.recipe_action_triggered`: this feature is specifically about
    the pre-login redirect, so the trigger URL is prepared but not visited yet - the
    scenarios themselves decide whether to request it without following redirects
    (unauthenticated) or navigate all the way through login (authenticated).
    """
    recipe_ingredients = [build_ingredient(quantity, name) for quantity, name in datatable]
    slug = slugify(recipe_name)
    stub_recipe(requests_mock, config, slug, recipe_name, recipe_ingredients)
    return {"url": f"{live_server.url('/recipes/action')}?slug={slug}"}


@then("I am redirected to log in")
def redirected_to_log_in(page, triggered):
    response = page.request.get(triggered["url"], max_redirects=0)
    assert response.status == 302
    assert response.headers["location"] == "/auth/login"


@then("I see the shopping lists to choose from")
def see_shopping_lists_to_choose_from(triggered):
    assert triggered["response"].status == 200


@when("I complete login with the identity provider", target_fixture="triggered")
def complete_login(page, triggered):
    """A real navigation to the trigger URL completes the whole login round-trip in one
    go: mock-oauth2-server's interactive login page is disabled (see
    `oidc_container.py`), so there's no separate click to drive - the browser follows
    the bridge's redirect to `/auth/login`, the identity provider's auto-issued
    authorization code, and the callback back to the originally requested page.
    """
    response = page.goto(triggered["url"])
    return {**triggered, "response": response}
