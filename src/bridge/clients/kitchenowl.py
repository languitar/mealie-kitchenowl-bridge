import requests


class KitchenOwlClient:
    """Thin wrapper around the KitchenOwl HTTP API."""

    def __init__(self, base_url: str, api_token: str, household_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.household_id = household_id

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_token}"}

    def get_shopping_lists(self) -> list[dict]:
        response = requests.get(
            f"{self.base_url}/api/household/{self.household_id}/shoppinglist",
            headers=self._headers(),
        )
        response.raise_for_status()
        return [{"id": item["id"], "name": item["name"]} for item in response.json()]

    def get_items(self) -> list[dict]:
        """List every item in the household's catalog (across all shopping lists)."""
        response = requests.get(
            f"{self.base_url}/api/household/{self.household_id}/item",
            headers=self._headers(),
        )
        response.raise_for_status()
        return [{"id": item["id"], "name": item["name"]} for item in response.json()]

    def _find_or_create_item_id(self, name: str) -> int:
        """Resolve a household item's id by exact name, creating it if it doesn't exist yet.

        `/item/search` does fuzzy (Levenshtein) matching, so results are
        filtered down to an exact, case-insensitive match here.
        """
        response = requests.get(
            f"{self.base_url}/api/household/{self.household_id}/item/search",
            headers=self._headers(),
            params={"query": name},
        )
        response.raise_for_status()
        for candidate in response.json():
            if candidate["name"].casefold() == name.casefold():
                return candidate["id"]

        response = requests.post(
            f"{self.base_url}/api/household/{self.household_id}/item",
            headers=self._headers(),
            json={"name": name},
        )
        response.raise_for_status()
        return response.json()["id"]

    def add_shopping_list_item(
        self,
        list_id: int,
        name: str,
        description: str | None = None,
        item_id: int | None = None,
    ) -> None:
        """Add an item to a shopping list, merging its quantity if the item is already there.

        Uses the `recipeitems` endpoint (the same one KitchenOwl's own recipe
        import feature uses) rather than `add-item-by-name`, since the latter
        silently ignores the description on an item that's already on the
        list. `recipeitems` instead merges same-unit quantities (with SI
        weight/volume conversion) and otherwise appends the new quantity as a
        second comma-separated entry in the description - KitchenOwl's own
        `description_merger` logic, not reimplemented here.

        Pass `item_id` to target a specific, already-known catalog item
        (e.g. one the user picked as a match) instead of resolving `name` to
        an item via exact lookup/creation.
        """
        resolved_item_id = item_id if item_id is not None else self._find_or_create_item_id(name)
        response = requests.post(
            f"{self.base_url}/api/shoppinglist/{list_id}/recipeitems",
            headers=self._headers(),
            json={
                "items": [
                    {"id": resolved_item_id, "name": name, "description": description or ""}
                ]
            },
        )
        response.raise_for_status()
