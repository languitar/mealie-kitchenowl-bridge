class KitchenOwlClient:
    """Thin wrapper around the KitchenOwl HTTP API.

    Only connection wiring exists so far; methods are added as real
    features are fed into the BDD workflow (see AGENTS.md).
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def add_shopping_list_item(self, list_id: str, name: str):
        raise NotImplementedError("Implement when the first shopping-list-push feature lands")
