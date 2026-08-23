from dataclasses import replace
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from pytest_bdd import scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/authentication.feature")


def parse_redirect_query(location: str) -> dict[str, str]:
    """Pull the query parameters (e.g. `state`, `nonce`) off a redirect's Location header."""
    query = parse_qs(urlparse(location).query)
    return {key: values[0] for key, values in query.items()}


@pytest.fixture
def config(kitchenowl_config, oidc_server):
    return replace(
        kitchenowl_config,
        oidc_issuer=oidc_server.issuer_url,
        oidc_client_id="bridge-tests-client",
        oidc_client_secret="bridge-tests-secret",  # noqa: S106
    )


@then("I am redirected to log in")
def redirected_to_log_in(triggered):
    response = triggered["response"]
    assert response.status_code == 302
    assert response.location == "/auth/login"


@then("I see the shopping lists to choose from")
def see_shopping_lists_to_choose_from(triggered):
    assert triggered["response"].status_code == 200


@when("I complete login with the identity provider", target_fixture="triggered")
def complete_login(running_app, triggered):
    login_response = running_app.get(triggered["response"].location)
    authorize_response = requests.get(login_response.location, allow_redirects=False, timeout=5)
    callback_params = parse_redirect_query(authorize_response.headers["Location"])

    callback_response = running_app.get("/auth/callback", query_string=callback_params)
    final_response = running_app.get(callback_response.location)
    return {**triggered, "response": final_response}
