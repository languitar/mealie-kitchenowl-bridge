from pytest_bdd import scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/health_check.feature")


@when("I request the health endpoint", target_fixture="response")
def request_health_endpoint(running_app):
    return running_app.get("/healthz")


@then("the response indicates the service is healthy")
def response_is_healthy(response):
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
