from flask import Blueprint, current_app, request

from bridge.clients.mealie import MealieClient
from bridge.errors import render_error
from bridge.ingredients import parse_ingredient
from bridge.routes.review import render_shopping_list_selection

trigger_bp = Blueprint("trigger", __name__)


@trigger_bp.get("/recipes/action")
def recipe_action():
    """Entry point for Mealie's "Link"-type recipe action (see AGENTS.md).

    Mealie's "Post"-type action can't redirect the user's browser - it's
    executed entirely server-side by Mealie's own backend, invisible to the
    browser. Only "Link" actions cause a real browser navigation, but they
    carry no recipe payload, only whatever's templated into the configured
    URL - so this fetches the triggering recipe from Mealie's own API by
    slug instead of reading it from a request body.

    This route carries no auth check of its own - reaching it at all
    requires an authenticated session, enforced app-wide by `bridge.auth`.

    Errors render as HTML, not JSON - this URL is opened directly in the
    user's browser (see AGENTS.md's Mealie trigger shape note), not called
    by server-side code that would parse a JSON body.
    """
    config = current_app.config["BRIDGE_CONFIG"]
    slug = request.args.get("slug", "")
    if not slug:
        return render_error("This link is missing a recipe.", 400)

    recipe = MealieClient(config.mealie_url, config.mealie_api_token).get_recipe(slug)
    ingredients = [parse_ingredient(ingredient) for ingredient in recipe["recipeIngredient"]]
    return render_shopping_list_selection(recipe["name"], ingredients)
