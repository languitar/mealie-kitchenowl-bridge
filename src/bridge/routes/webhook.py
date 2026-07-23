from flask import Blueprint, request

from bridge.routes.review import render_shopping_list_selection

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.post("/recipes/action")
def recipe_action():
    """Entry point for Mealie's "Post"-type recipe action (see AGENTS.md).

    Mealie POSTs the full recipe JSON (its `Recipe` schema, including
    `recipeIngredient` with pre-formatted `display` strings) to this URL when
    the action is triggered - no separate call back to Mealie's API is
    needed since the ingredients are already in the body.
    """
    recipe = request.get_json()
    ingredients = [ingredient["display"] for ingredient in recipe["recipeIngredient"]]
    return render_shopping_list_selection(recipe["name"], ingredients)
