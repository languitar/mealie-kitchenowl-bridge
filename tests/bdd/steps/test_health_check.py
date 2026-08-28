from pytest_bdd import scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/health_check.feature")


@when("I request the health endpoint", target_fixture="response")
def request_health_endpoint(live_server, page):
    return page.request.get(live_server.url("/healthz"))


@then("the response indicates the service is healthy")
def response_is_healthy(response):
    assert response.status == 200
    assert response.json() == {"status": "ok"}
