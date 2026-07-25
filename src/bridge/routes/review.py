from flask import Blueprint, current_app, render_template, request
from werkzeug.datastructures import MultiDict

from bridge.clients.kitchenowl import KitchenOwlClient
from bridge.ingredients import Ingredient
from bridge.matching import KitchenOwlItem, find_best_match

_NEW_ITEM_CHOICE = "new"

review_bp = Blueprint("review", __name__)


def _kitchenowl_client() -> KitchenOwlClient:
    config = current_app.config["BRIDGE_CONFIG"]
    return KitchenOwlClient(
        config.kitchenowl_url, config.kitchenowl_api_token, config.kitchenowl_household_id
    )


def _shopping_list_name(client: KitchenOwlClient, list_id: int) -> str | None:
    return next((sl["name"] for sl in client.get_shopping_lists() if sl["id"] == list_id), None)


def render_shopping_list_selection(recipe_name: str, ingredients: list[Ingredient]):
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


def _ingredients_from_form(form: MultiDict) -> list[Ingredient]:
    """Reassemble ingredients (with quantity) from the round-tripped form fields.

    Each ingredient's quantity travels in its own `quantity:<name>` field
    (see the templates) rather than a same-order parallel list, so that
    deselecting an ingredient's checkbox can't desynchronize name/quantity
    pairs.
    """
    return [
        Ingredient(name=name, quantity=form.get(f"quantity:{name}") or None)
        for name in form.getlist("ingredient")
    ]


@review_bp.post("/shopping-lists/<int:list_id>")
def review_ingredients(list_id: int):
    """Render the ingredient review screen, all ingredients pre-selected.

    Ingredients are again round-tripped through the form (this time as
    checkboxes) rather than kept server-side. Each ingredient is also
    matched against the household's existing KitchenOwl items (tolerating
    plural/inflected forms and minor spelling differences - see
    `bridge.matching`), pre-selecting that match on the review screen while
    still letting the user pick a different item or create a new one.
    """
    client = _kitchenowl_client()
    ingredients = _ingredients_from_form(request.form)
    items = [KitchenOwlItem(id=item["id"], name=item["name"]) for item in client.get_items()]
    matches = {
        ingredient.name: find_best_match(ingredient.name, items) for ingredient in ingredients
    }
    return render_template(
        "select_ingredients.html",
        list_id=list_id,
        shopping_list_name=_shopping_list_name(client, list_id),
        ingredients=ingredients,
        items=items,
        matches=matches,
    )


@review_bp.post("/shopping-lists/<int:list_id>/confirm")
def push_to_shopping_list(list_id: int):
    ingredients = _ingredients_from_form(request.form)
    client = _kitchenowl_client()
    for ingredient in ingredients:
        choice = request.form.get(f"item_choice:{ingredient.name}", _NEW_ITEM_CHOICE)
        item_id = int(choice) if choice != _NEW_ITEM_CHOICE else None
        client.add_shopping_list_item(list_id, ingredient.name, ingredient.quantity, item_id)

    return render_template(
        "shopping_list_confirmation.html",
        shopping_list_name=_shopping_list_name(client, list_id),
        ingredients=ingredients,
    )
