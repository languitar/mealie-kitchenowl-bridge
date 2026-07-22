"""Step definitions shared across multiple .feature files.

Add new capability-specific steps to a dedicated module next to the
feature they belong to; only promote a step here once a second feature
needs it verbatim.
"""

from pytest_bdd import given


@given("the bridge is running", target_fixture="running_app")
def bridge_is_running(client):
    return client
