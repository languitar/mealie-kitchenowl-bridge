import hmac

from flask import Blueprint, current_app, jsonify, request

from bridge.ingredients import parse_ingredient
from bridge.routes.review import render_shopping_list_selection

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.post("/recipes/action")
def recipe_action():
    """Entry point for Mealie's "Post"-type recipe action (see AGENTS.md).

    Mealie POSTs the full recipe JSON (its `Recipe` schema, including
    `recipeIngredient` with pre-formatted `display` strings) to this URL when
    the action is triggered - no separate call back to Mealie's API is
    needed since the ingredients are already in the body. Mealie can't be
    configured with custom headers for this call, so the shared webhook
    secret travels as a `token` query parameter instead.
    """
    config = current_app.config["BRIDGE_CONFIG"]
    provided_token = request.args.get("token", "")
    if not config.webhook_token or not hmac.compare_digest(provided_token, config.webhook_token):
        return jsonify(error="unauthorized"), 401

    recipe = request.get_json()
    ingredients = [parse_ingredient(ingredient) for ingredient in recipe["recipeIngredient"]]
    return render_shopping_list_selection(recipe["name"], ingredients)
