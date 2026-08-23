"""Runs a real OIDC identity provider in a container for acceptance-level tests.

We test the login flow against a real server instead of stubbing HTTP calls
(see AGENTS.md) so the suite can't miss bugs in how the app's actual OIDC
client code (Authlib) talks to a real discovery document, token endpoint, and
JWKS. mock-oauth2-server is purpose-built for this: it speaks real OIDC but
lets the interactive login page be disabled entirely, so the whole
authorization-code flow can still be driven with plain HTTP calls.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import requests
from testcontainers.core.container import DockerContainer

_IMAGE = "ghcr.io/navikt/mock-oauth2-server:6.0.1"
_PORT = 8080
_ISSUER_ID = "default"
_READY_TIMEOUT_SECONDS = 15
_JSON_CONFIG = {
    "interactiveLogin": False,
    "tokenCallbacks": [
        {
            "issuerId": _ISSUER_ID,
            "requestMappings": [
                {
                    "requestParam": "code",
                    "match": "*",
                    "claims": {
                        "sub": "test-user",
                        "aud": ["${clientId}"],
                        "email": "test-user@example.com",
                    },
                }
            ],
        }
    ],
}


@dataclass
class OidcTestServer:
    """A running mock-oauth2-server instance, with interactive login disabled."""

    base_url: str

    @property
    def issuer_url(self) -> str:
        return f"{self.base_url}/{_ISSUER_ID}"


def _wait_until_ready(issuer_url: str) -> None:
    deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{issuer_url}/.well-known/openid-configuration", timeout=1)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException as error:
            last_error = error
        time.sleep(0.5)
    raise TimeoutError(
        f"OIDC container did not become ready within {_READY_TIMEOUT_SECONDS}s"
    ) from last_error


def start_oidc_container() -> tuple[DockerContainer, OidcTestServer]:
    """Start a mock-oauth2-server container and wait for it to become ready.

    Returns the container (caller owns its lifecycle) and a server handle.
    """
    container = (
        DockerContainer(_IMAGE)
        .with_exposed_ports(_PORT)
        .with_env("JSON_CONFIG", json.dumps(_JSON_CONFIG))
    )
    container.start()

    host = container.get_container_host_ip()
    port = container.get_exposed_port(_PORT)
    base_url = f"http://{host}:{port}"
    server = OidcTestServer(base_url=base_url)

    _wait_until_ready(server.issuer_url)

    return container, server
