import requests


class MealieClient:
    """Thin wrapper around the Mealie HTTP API."""

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_token}"}

    def get_recipe(self, slug: str) -> dict:
        response = requests.get(f"{self.base_url}/api/recipes/{slug}", headers=self._headers())
        response.raise_for_status()
        return response.json()
