"""Runs a real KitchenOwl instance in a container for acceptance-level tests.

We test against the real API instead of mocking it (see AGENTS.md) so the test
suite can't drift from how KitchenOwl actually behaves.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from testcontainers.core.container import DockerContainer

_IMAGE = "tombursch/kitchenowl:v0.7.9"
_PORT = 8080
_HEALTH_PATH = "/api/health/8M4F88S8ooi4sMbLBfkkV7ctWwgibW6V"
_READY_TIMEOUT_SECONDS = 60
_ADMIN_USERNAME = "bridge-tests"
_ADMIN_PASSWORD = "bridge-tests-password"  # noqa: S105 (throwaway container, not a secret)
_ADMIN_DEVICE = "bridge-tests"


@dataclass
class KitchenOwlTestServer:
    """A running KitchenOwl instance, onboarded with one admin user."""

    base_url: str
    admin_token: str

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.admin_token}"}

    def create_household(self, name: str) -> int:
        response = requests.post(
            f"{self.base_url}/api/household",
            headers=self._headers(),
            json={"name": name},
        )
        response.raise_for_status()
        return response.json()["id"]

    def create_shopping_list(self, household_id: int, name: str) -> int:
        response = requests.post(
            f"{self.base_url}/api/household/{household_id}/shoppinglist",
            headers=self._headers(),
            json={"name": name},
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_shopping_list_items(self, household_id: int, list_id: int) -> list[dict]:
        response = requests.get(
            f"{self.base_url}/api/household/{household_id}/shoppinglist",
            headers=self._headers(),
        )
        response.raise_for_status()
        shopping_list = next(sl for sl in response.json() if sl["id"] == list_id)
        return shopping_list["items"]


def _wait_until_ready(base_url: str) -> None:
    deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}{_HEALTH_PATH}", timeout=1)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException as error:
            last_error = error
        time.sleep(0.5)
    raise TimeoutError(
        f"KitchenOwl container did not become ready within {_READY_TIMEOUT_SECONDS}s"
    ) from last_error


def _onboard_admin(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/onboarding",
        json={
            "name": "Bridge Tests",
            "username": _ADMIN_USERNAME,
            "password": _ADMIN_PASSWORD,
            "device": _ADMIN_DEVICE,
        },
    )
    response.raise_for_status()
    access_token = response.json()["access_token"]

    response = requests.post(
        f"{base_url}/api/auth/llt",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"device": _ADMIN_DEVICE},
    )
    response.raise_for_status()
    return response.json()["longlived_token"]


def start_kitchenowl_container() -> tuple[DockerContainer, KitchenOwlTestServer]:
    """Start a KitchenOwl container, wait for it, and onboard one admin user.

    Returns the container (caller owns its lifecycle) and a server handle
    already authenticated as that admin.
    """
    container = DockerContainer(_IMAGE).with_exposed_ports(_PORT).with_env(
        "JWT_SECRET_KEY", "bridge-tests-secret"
    )
    container.start()

    host = container.get_container_host_ip()
    port = container.get_exposed_port(_PORT)
    base_url = f"http://{host}:{port}"

    _wait_until_ready(base_url)
    admin_token = _onboard_admin(base_url)

    return container, KitchenOwlTestServer(base_url=base_url, admin_token=admin_token)
