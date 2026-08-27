from playwright.sync_api import expect
from pytest_bdd import scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/home_page.feature")


@when("I open the home page", target_fixture="opened_page")
def open_home_page(page, live_server):
    page.goto(live_server.url("/"))
    return page


@then("I see the bridge's title")
def see_bridge_title(opened_page):
    expect(opened_page).to_have_title("Mealie ↔ KitchenOwl Bridge")
