"""Runs a real Mealie instance in a container for acceptance-level tests.

We test the trigger flow against the real API and a real browser click
instead of mocking it (see AGENTS.md) so the suite can't miss bugs that only
show up in how Mealie's frontend actually drives a recipe action - see
`mealie_recipe_trigger.feature`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from testcontainers.core.container import DockerContainer

_IMAGE = "ghcr.io/mealie-recipes/mealie:v3.22.0"
_PORT = 9000
_READY_PATH = "/api/app/about"
_READY_TIMEOUT_SECONDS = 90
_DEFAULT_ADMIN_EMAIL = "changeme@example.com"
_DEFAULT_ADMIN_PASSWORD = "MyPassword"  # noqa: S105 (throwaway container, not a secret)
_API_TOKEN_NAME = "bridge-tests"


@dataclass
class MealieTestServer:
    """A running Mealie instance, authenticated as its default admin user."""

    base_url: str
    admin_token: str
    group_slug: str

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.admin_token}"}

    def recipe_url(self, slug: str) -> str:
        return f"{self.base_url}/g/{self.group_slug}/r/{slug}"

    def create_recipe(self, name: str, ingredient_names: list[str]) -> str:
        """Create a recipe with the given name and (free-text) ingredient names.

        Two-step, mirroring Mealie's own API: creating by name returns a
        slug, then the full ingredient list is set via a follow-up PUT with
        the fetched recipe body.
        """
        response = requests.post(
            f"{self.base_url}/api/recipes",
            headers=self._headers(),
            json={"name": name},
        )
        response.raise_for_status()
        slug = response.json()

        response = requests.get(f"{self.base_url}/api/recipes/{slug}", headers=self._headers())
        response.raise_for_status()
        recipe = response.json()
        recipe["recipeIngredient"] = [
            {
                "food": None,
                "unit": None,
                "quantity": None,
                "note": ingredient_name,
                "display": ingredient_name,
            }
            for ingredient_name in ingredient_names
        ]

        response = requests.put(
            f"{self.base_url}/api/recipes/{slug}", headers=self._headers(), json=recipe
        )
        response.raise_for_status()
        return slug

    def create_link_action(self, title: str, url: str) -> int:
        response = requests.post(
            f"{self.base_url}/api/households/recipe-actions",
            headers=self._headers(),
            json={"action_type": "link", "title": title, "url": url},
        )
        response.raise_for_status()
        return response.json()["id"]


def _wait_until_ready(base_url: str) -> None:
    deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}{_READY_PATH}", timeout=1)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException as error:
            last_error = error
        time.sleep(0.5)
    raise TimeoutError(
        f"Mealie container did not become ready within {_READY_TIMEOUT_SECONDS}s"
    ) from last_error


def _login(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/auth/token",
        data={"username": _DEFAULT_ADMIN_EMAIL, "password": _DEFAULT_ADMIN_PASSWORD},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _mint_api_token(base_url: str, access_token: str) -> str:
    response = requests.post(
        f"{base_url}/api/users/api-tokens",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": _API_TOKEN_NAME},
    )
    response.raise_for_status()
    return response.json()["token"]


def _group_slug(base_url: str, access_token: str) -> str:
    response = requests.get(
        f"{base_url}/api/groups/self",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()["slug"]


def start_mealie_container() -> tuple[DockerContainer, MealieTestServer]:
    """Start a Mealie container, wait for it, and authenticate as its default admin.

    Mealie auto-creates a default admin user (`changeme@example.com` /
    `MyPassword`) on first boot, so - unlike KitchenOwl - no separate
    onboarding call is needed, just a login.

    Returns the container (caller owns its lifecycle) and a server handle
    already authenticated as that admin.
    """
    container = DockerContainer(_IMAGE).with_exposed_ports(_PORT)
    container.start()

    host = container.get_container_host_ip()
    port = container.get_exposed_port(_PORT)
    base_url = f"http://{host}:{port}"

    _wait_until_ready(base_url)
    access_token = _login(base_url)
    admin_token = _mint_api_token(base_url, access_token)
    group_slug = _group_slug(base_url, access_token)

    return container, MealieTestServer(
        base_url=base_url, admin_token=admin_token, group_slug=group_slug
    )
