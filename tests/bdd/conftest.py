# Shared BDD-level fixtures beyond what tests/conftest.py provides.
#
# `requests_mock` (from the requests-mock package) is available automatically
# as a pytest fixture for stubbing calls to the real Mealie API - acceptance
# scenarios should never hit live services. KitchenOwl is different: scenarios
# that exercise it run against a real instance (see `kitchenowl_server` below
# and AGENTS.md) rather than a mock, so the suite can't drift from its actual
# API behavior.

import threading
from dataclasses import dataclass

import pytest
from werkzeug.serving import make_server

from bridge.config import Config

from .kitchenowl_container import KitchenOwlTestServer, start_kitchenowl_container


class _LiveServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def url(self, path: str = "/") -> str:
        return f"http://{self.host}:{self.port}{path}"


@pytest.fixture
def live_server(app):
    """Serve `app` on a real port in a background thread.

    Overrides pytest-flask's own `live_server` fixture, which starts the app
    in a subprocess via `multiprocessing.Process` - that breaks under Python
    3.14's `forkserver` default start method because its process target is
    an unpicklable local closure. A plain thread avoids the whole problem.
    """
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    try:
        yield _LiveServer(*server.server_address)
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture(scope="session")
def kitchenowl_server():
    """Start one real KitchenOwl container for the whole test session.

    Only tests that request this (directly or via `kitchenowl_household`) pay
    the container startup cost - `health_check`/`home_page` scenarios never
    touch it.
    """
    container, server = start_kitchenowl_container()
    try:
        yield server
    finally:
        container.stop()


@dataclass
class KitchenOwlHousehold:
    server: KitchenOwlTestServer
    id: int


@pytest.fixture
def kitchenowl_household(kitchenowl_server):
    """A fresh KitchenOwl household per test, for isolation without restarting
    the container - each household starts with its own "Default" shopping
    list and no items shared with other tests.
    """
    household_id = kitchenowl_server.create_household("Bridge Test Household")
    return KitchenOwlHousehold(server=kitchenowl_server, id=household_id)


@pytest.fixture
def kitchenowl_config(config, kitchenowl_household) -> Config:
    """`config` with KitchenOwl connection details pointed at the real per-test household.

    Opt-in (not a blanket override of `config`) so scenarios that don't need
    KitchenOwl (health_check, home_page) don't pay the container startup cost -
    see AGENTS.md's BDD workflow notes on testing against a real KitchenOwl.
    """
    return Config(
        kitchenowl_url=kitchenowl_household.server.base_url,
        kitchenowl_api_token=kitchenowl_household.server.admin_token,
        kitchenowl_household_id=str(kitchenowl_household.id),
        webhook_token=config.webhook_token,
    )
