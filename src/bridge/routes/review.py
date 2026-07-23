from flask import Blueprint, current_app, render_template, request

from bridge.clients.kitchenowl import KitchenOwlClient

review_bp = Blueprint("review", __name__)


def _kitchenowl_client() -> KitchenOwlClient:
    config = current_app.config["BRIDGE_CONFIG"]
    return KitchenOwlClient(
        config.kitchenowl_url, config.kitchenowl_api_token, config.kitchenowl_household_id
    )


def render_shopping_list_selection(recipe_name: str, ingredients: list[str]):
    """Render the dialog for picking which KitchenOwl shopping list to push to.

    Ingredients are round-tripped through hidden form fields rather than kept
    server-side - see AGENTS.md's no-persistence convention.
    """
    shopping_lists = _kitchenowl_client().get_shopping_lists()
    return render_template(
        "select_shopping_list.html",
        recipe_name=recipe_name,
        ingredients=ingredients,
        shopping_lists=shopping_lists,
    )


@review_bp.post("/shopping-lists/<int:list_id>")
def push_to_shopping_list(list_id: int):
    ingredients = request.form.getlist("ingredient")
    client = _kitchenowl_client()
    for ingredient in ingredients:
        client.add_shopping_list_item(list_id, ingredient)

    shopping_list_name = next(
        (sl["name"] for sl in client.get_shopping_lists() if sl["id"] == list_id),
        None,
    )
    return render_template(
        "shopping_list_confirmation.html",
        shopping_list_name=shopping_list_name,
        ingredients=ingredients,
    )
