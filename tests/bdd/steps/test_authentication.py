import pytest
from pytest_bdd import scenarios, then, when

from ..fake_oidc import parse_redirect_query
from .common import *  # noqa: F401,F403

scenarios("../features/authentication.feature")


@pytest.fixture
def config(kitchenowl_config):
    return kitchenowl_config


@then("I am redirected to log in")
def redirected_to_log_in(triggered):
    response = triggered["response"]
    assert response.status_code == 302
    assert response.location == "/auth/login"


@then("I see the shopping lists to choose from")
def see_shopping_lists_to_choose_from(triggered):
    assert triggered["response"].status_code == 200


@when("I complete login with the identity provider", target_fixture="triggered")
def complete_login(running_app, triggered, requests_mock, oidc_provider):
    login_response = running_app.get(triggered["response"].location)
    authorize_params = parse_redirect_query(login_response.location)

    oidc_provider.stub_successful_login(requests_mock, nonce=authorize_params["nonce"])

    callback_response = running_app.get(
        "/auth/callback",
        query_string={"code": "fake-code", "state": authorize_params["state"]},
    )
    final_response = running_app.get(callback_response.location)
    return {**triggered, "response": final_response}
