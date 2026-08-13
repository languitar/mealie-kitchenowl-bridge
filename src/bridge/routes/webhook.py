import hmac

from flask import Blueprint, current_app, jsonify, request

from bridge.clients.mealie import MealieClient
from bridge.ingredients import parse_ingredient
from bridge.routes.review import render_shopping_list_selection

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.get("/recipes/action")
def recipe_action():
    """Entry point for Mealie's "Link"-type recipe action (see AGENTS.md).

    Mealie's "Post"-type action can't redirect the user's browser - it's
    executed entirely server-side by Mealie's own backend, invisible to the
    browser. Only "Link" actions cause a real browser navigation, but they
    carry no recipe payload, only whatever's templated into the configured
    URL - so this fetches the triggering recipe from Mealie's own API by
    slug instead of reading it from a request body. Mealie can't be
    configured with custom headers for this call, so the shared webhook
    secret travels as a `token` query parameter instead.
    """
    config = current_app.config["BRIDGE_CONFIG"]
    provided_token = request.args.get("token", "")
    if not config.webhook_token or not hmac.compare_digest(provided_token, config.webhook_token):
        return jsonify(error="unauthorized"), 401

    slug = request.args.get("slug", "")
    if not slug:
        return jsonify(error="missing slug"), 400

    recipe = MealieClient(config.mealie_url, config.mealie_api_token).get_recipe(slug)
    ingredients = [parse_ingredient(ingredient) for ingredient in recipe["recipeIngredient"]]
    return render_shopping_list_selection(recipe["name"], ingredients)
