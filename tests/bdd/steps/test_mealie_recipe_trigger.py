from dataclasses import replace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/mealie_recipe_trigger.feature")

# Mealie's recipe-action menu button has no accessible name (an icon-only
# Vuetify button) - matched by its "dots-vertical" icon path instead.
_RECIPE_MENU_BUTTON = 'button:has(path[d^="M12,16A2,2"])'


@pytest.fixture
def config(kitchenowl_config, mealie_server):
    """`kitchenowl_config` further pointed at the real per-session Mealie container.

    This scenario is the only one that needs both real backends live at
    once, since it drives the trigger through an actual Mealie browser click
    rather than a direct HTTP call - see AGENTS.md/the plan for why that's
    the point of this scenario.
    """
    return replace(
        kitchenowl_config,
        mealie_url=mealie_server.base_url,
        mealie_api_token=mealie_server.admin_token,
    )


@given(
    parsers.parse('a real Mealie recipe "{recipe_name}" with the ingredient "{ingredient_name}"'),
    target_fixture="mealie_recipe",
)
def real_mealie_recipe(mealie_server, recipe_name, ingredient_name):
    slug = mealie_server.create_recipe(recipe_name, [ingredient_name])
    return {"slug": slug, "name": recipe_name}


@given("the bridge's recipe action is configured on that recipe in Mealie")
def bridge_action_configured(mealie_server, live_server):
    action_url = f"{live_server.url('/recipes/action')}?slug=${{slug}}"
    mealie_server.create_link_action("Send to KitchenOwl", action_url)


@when("I open the recipe in Mealie and trigger its action", target_fixture="triggered_popup")
def open_recipe_and_trigger_action(page, mealie_server, mealie_recipe):
    page.goto(mealie_server.base_url)
    page.fill('input[name="username"]', "changeme@example.com")
    page.fill('input[name="password"]', "MyPassword")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")

    page.goto(mealie_server.recipe_url(mealie_recipe["slug"]))
    page.wait_for_load_state("networkidle")
    page.locator(_RECIPE_MENU_BUTTON).first.click()

    with page.expect_popup() as popup_info:
        page.get_by_text("Send to KitchenOwl").click()
    popup = popup_info.value
    popup.wait_for_load_state("networkidle")
    return popup


@then(
    parsers.parse(
        "a new browser tab shows the bridge's shopping list selection for \"{recipe_name}\""
    )
)
def see_bridge_selection_screen(triggered_popup, recipe_name):
    assert recipe_name in triggered_popup.content()
