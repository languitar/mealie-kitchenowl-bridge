# Shared BDD-level fixtures beyond what tests/conftest.py provides.
#
# `requests_mock` (from the requests-mock package) is available automatically
# as a pytest fixture for stubbing calls to the real Mealie/KitchenOwl APIs -
# acceptance scenarios should never hit live services.

import threading

import pytest
from werkzeug.serving import make_server


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
