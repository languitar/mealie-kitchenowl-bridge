#!/usr/bin/env python3
"""Seeds the local dev stack (docker-compose.yml) with realistic test data.

Populates Mealie with a few recipes and a "Push to KitchenOwl" recipe action,
and KitchenOwl with a household, a shopping list, and some catalog items -
then writes the tokens it minted to the seed_env volume (/seed/env), which
the bridge container sources automatically on startup, and to .env (from
.env.dev-stack.example) for running the bridge with `uv run flask` instead.
See README's "Local dev stack" section.

Safe to re-run: existing recipes/households/items are detected and left
alone, only the token files get rewritten with fresh tokens each time.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_TEMPLATE = REPO_ROOT / ".env.dev-stack.example"
ENV_FILE = REPO_ROOT / ".env"
SEED_ENV_FILE = Path("/seed/env")

MEALIE_URL = "http://127.0.0.1:9000"
_MEALIE_ADMIN_EMAIL = "changeme@example.com"
_MEALIE_ADMIN_PASSWORD = "MyPassword"  # noqa: S105 (throwaway dev-stack container)
_MEALIE_API_TOKEN_NAME = "dev-stack-bridge"

KITCHENOWL_URL = "http://127.0.0.1:8080"
_KITCHENOWL_USERNAME = "devstack"
_KITCHENOWL_PASSWORD = "devstack-password"  # noqa: S105 (throwaway dev-stack container)
_KITCHENOWL_DEVICE = "dev-stack-seed"
_KITCHENOWL_HOUSEHOLD_NAME = "Home"
_KITCHENOWL_SHOPPING_LIST_NAME = "Groceries"
_KITCHENOWL_CATALOG_ITEMS = ["Onion", "Garlic", "Olive Oil", "Salt"]

BRIDGE_URL = "http://127.0.0.1:5050"

_RECIPES = [
    (
        "Spaghetti Bolognese",
        [
            "500 g ground beef",
            "1 onion, diced",
            "2 cloves garlic, minced",
            "400 g canned tomatoes",
            "2 tbsp olive oil",
            "400 g spaghetti",
            "Salt and pepper to taste",
        ],
    ),
    (
        "Greek Salad",
        [
            "2 large tomatoes",
            "1 cucumber",
            "1 red onion",
            "200 g feta cheese",
            "100 g kalamata olives",
            "3 tbsp olive oil",
            "1 tsp dried oregano",
        ],
    ),
    (
        "Chicken Curry",
        [
            "500 g chicken breast",
            "1 onion, chopped",
            "2 cloves garlic, minced",
            "1 tbsp curry powder",
            "400 ml coconut milk",
            "1 tbsp vegetable oil",
            "Salt to taste",
        ],
    ),
]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _wait_until_ready(name: str, url: str, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if requests.get(url, timeout=2).status_code < 500:
                return
        except requests.exceptions.RequestException as error:
            last_error = error
        time.sleep(1)
    raise TimeoutError(f"{name} did not become ready within {timeout}s") from last_error


def seed_mealie() -> str:
    print("Waiting for Mealie...")
    _wait_until_ready("Mealie", f"{MEALIE_URL}/api/app/about")

    response = requests.post(
        f"{MEALIE_URL}/api/auth/token",
        data={"username": _MEALIE_ADMIN_EMAIL, "password": _MEALIE_ADMIN_PASSWORD},
    )
    response.raise_for_status()
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    for name, ingredient_names in _RECIPES:
        slug = _slugify(name)
        if requests.get(f"{MEALIE_URL}/api/recipes/{slug}", headers=headers).status_code == 200:
            print(f"  Recipe '{name}' already exists, skipping.")
            continue

        response = requests.post(f"{MEALIE_URL}/api/recipes", headers=headers, json={"name": name})
        response.raise_for_status()
        slug = response.json()

        response = requests.get(f"{MEALIE_URL}/api/recipes/{slug}", headers=headers)
        response.raise_for_status()
        recipe = response.json()
        recipe["recipeIngredient"] = [
            {"food": None, "unit": None, "quantity": None, "note": n, "display": n}
            for n in ingredient_names
        ]
        response = requests.put(
            f"{MEALIE_URL}/api/recipes/{slug}", headers=headers, json=recipe
        )
        response.raise_for_status()
        print(f"  Created recipe '{name}'.")

    action_url = f"{BRIDGE_URL}/recipes/action?slug=" + "${slug}"
    response = requests.get(f"{MEALIE_URL}/api/households/recipe-actions", headers=headers)
    response.raise_for_status()
    if not any(action["url"] == action_url for action in response.json()["items"]):
        requests.post(
            f"{MEALIE_URL}/api/households/recipe-actions",
            headers=headers,
            json={"action_type": "link", "title": "Push to KitchenOwl", "url": action_url},
        ).raise_for_status()
        print("  Created 'Push to KitchenOwl' recipe action.")
    else:
        print("  Recipe action already exists, skipping.")

    response = requests.post(
        f"{MEALIE_URL}/api/users/api-tokens",
        headers=headers,
        json={"name": _MEALIE_API_TOKEN_NAME},
    )
    response.raise_for_status()
    return response.json()["token"]


def seed_kitchenowl() -> tuple[str, int]:
    print("Waiting for KitchenOwl...")
    _wait_until_ready(
        "KitchenOwl", f"{KITCHENOWL_URL}/api/health/8M4F88S8ooi4sMbLBfkkV7ctWwgibW6V"
    )

    response = requests.post(
        f"{KITCHENOWL_URL}/api/onboarding",
        json={
            "name": "Dev Stack",
            "username": _KITCHENOWL_USERNAME,
            "password": _KITCHENOWL_PASSWORD,
            "device": _KITCHENOWL_DEVICE,
        },
    )
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("  Onboarded KitchenOwl admin user.")
    else:
        response = requests.post(
            f"{KITCHENOWL_URL}/api/auth",
            json={
                "username": _KITCHENOWL_USERNAME,
                "password": _KITCHENOWL_PASSWORD,
                "device": _KITCHENOWL_DEVICE,
            },
        )
        response.raise_for_status()
        access_token = response.json()["access_token"]
        print("  KitchenOwl already onboarded, logged in instead.")

    response = requests.post(
        f"{KITCHENOWL_URL}/api/auth/llt",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"device": _KITCHENOWL_DEVICE},
    )
    response.raise_for_status()
    headers = {"Authorization": f"Bearer {response.json()['longlived_token']}"}

    response = requests.get(f"{KITCHENOWL_URL}/api/household", headers=headers)
    response.raise_for_status()
    household = next(
        (h for h in response.json() if h["name"] == _KITCHENOWL_HOUSEHOLD_NAME), None
    )
    if household is None:
        response = requests.post(
            f"{KITCHENOWL_URL}/api/household",
            headers=headers,
            json={"name": _KITCHENOWL_HOUSEHOLD_NAME},
        )
        response.raise_for_status()
        household_id = response.json()["id"]
        print(f"  Created household '{_KITCHENOWL_HOUSEHOLD_NAME}'.")
    else:
        household_id = household["id"]
        print(f"  Household '{_KITCHENOWL_HOUSEHOLD_NAME}' already exists, skipping.")

    response = requests.get(
        f"{KITCHENOWL_URL}/api/household/{household_id}/shoppinglist", headers=headers
    )
    response.raise_for_status()
    if not any(sl["name"] == _KITCHENOWL_SHOPPING_LIST_NAME for sl in response.json()):
        requests.post(
            f"{KITCHENOWL_URL}/api/household/{household_id}/shoppinglist",
            headers=headers,
            json={"name": _KITCHENOWL_SHOPPING_LIST_NAME},
        ).raise_for_status()
        print(f"  Created shopping list '{_KITCHENOWL_SHOPPING_LIST_NAME}'.")
    else:
        print(f"  Shopping list '{_KITCHENOWL_SHOPPING_LIST_NAME}' already exists, skipping.")

    response = requests.get(f"{KITCHENOWL_URL}/api/household/{household_id}/item", headers=headers)
    response.raise_for_status()
    existing_item_names = {item["name"].casefold() for item in response.json()}
    for item_name in _KITCHENOWL_CATALOG_ITEMS:
        if item_name.casefold() not in existing_item_names:
            requests.post(
                f"{KITCHENOWL_URL}/api/household/{household_id}/item",
                headers=headers,
                json={"name": item_name},
            ).raise_for_status()
    print(f"  Catalog items ready: {', '.join(_KITCHENOWL_CATALOG_ITEMS)}.")

    return headers["Authorization"].removeprefix("Bearer "), household_id


def write_seed_env(kitchenowl_token: str, kitchenowl_household_id: int, mealie_token: str) -> None:
    if not SEED_ENV_FILE.parent.is_dir():
        return
    SEED_ENV_FILE.write_text(
        f"KITCHENOWL_API_TOKEN={kitchenowl_token}\n"
        f"KITCHENOWL_HOUSEHOLD_ID={kitchenowl_household_id}\n"
        f"MEALIE_API_TOKEN={mealie_token}\n"
    )
    print(f"Wrote {SEED_ENV_FILE}")


def write_env(kitchenowl_token: str, kitchenowl_household_id: int, mealie_token: str) -> None:
    if not ENV_TEMPLATE.is_file():
        return
    template_first_line = ENV_TEMPLATE.read_text().splitlines()[:1]
    if ENV_FILE.exists() and ENV_FILE.read_text().splitlines()[:1] != template_first_line:
        print(
            f"{ENV_FILE} exists and doesn't look like it came from {ENV_TEMPLATE.name} "
            "- leaving it alone (looks like your real .env)."
        )
        return

    values = {
        "KITCHENOWL_API_TOKEN": kitchenowl_token,
        "KITCHENOWL_HOUSEHOLD_ID": str(kitchenowl_household_id),
        "MEALIE_API_TOKEN": mealie_token,
    }
    output_lines = []
    for line in ENV_TEMPLATE.read_text().splitlines(keepends=True):
        key = line.split("=", 1)[0]
        output_lines.append(f"{key}={values[key]}\n" if key in values else line)
    ENV_FILE.write_text("".join(output_lines))
    print(f"Wrote {ENV_FILE}")


def main() -> None:
    mealie_token = seed_mealie()
    kitchenowl_token, kitchenowl_household_id = seed_kitchenowl()
    write_seed_env(kitchenowl_token, kitchenowl_household_id, mealie_token)
    write_env(kitchenowl_token, kitchenowl_household_id, mealie_token)
    print()
    print("Dev stack seeded.")
    print(f"Open {MEALIE_URL} and log in with {_MEALIE_ADMIN_EMAIL} / {_MEALIE_ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
