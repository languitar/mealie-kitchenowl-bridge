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

    def add_shopping_list_item(self, list_id: int, name: str) -> None:
        response = requests.post(
            f"{self.base_url}/api/household/{self.household_id}"
            f"/shoppinglist/{list_id}/add-item-by-name",
            headers=self._headers(),
            json={"name": name},
        )
        response.raise_for_status()
