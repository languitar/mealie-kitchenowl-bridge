import pytest
from pytest_bdd import given, scenarios, then

from .common import *  # noqa: F401,F403

scenarios("../features/authentication.feature")


@pytest.fixture
def config(kitchenowl_config):
    return kitchenowl_config


@given("the webhook token is valid", target_fixture="webhook_token")
def webhook_token_is_valid(config):
    return config.webhook_token


@given("the webhook token is invalid", target_fixture="webhook_token")
def webhook_token_is_invalid(config):
    return config.webhook_token + "-wrong"


@then("the request is rejected as unauthorized")
def request_rejected_as_unauthorized(triggered):
    assert triggered["response"].status_code == 401


@then("I see the shopping lists to choose from")
def see_shopping_lists_to_choose_from(triggered):
    assert triggered["response"].status_code == 200
