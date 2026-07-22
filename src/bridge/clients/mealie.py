class MealieClient:
    """Thin wrapper around the Mealie HTTP API.

    Only connection wiring exists so far; methods are added as real
    features are fed into the BDD workflow (see AGENTS.md).
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def get_recipe(self, slug: str):
        raise NotImplementedError("Implement when the first recipe-fetching feature lands")
