from pytest_bdd import given, scenarios, then, when

scenarios("../features/home_page.feature")


@given("the bridge is running in a browser")
def bridge_is_running_in_a_browser(live_server):
    pass


@when("I open the home page", target_fixture="opened_page")
def open_home_page(page, live_server):
    page.goto(live_server.url("/"))
    return page


@then("I see the bridge's title")
def see_bridge_title(opened_page):
    assert opened_page.title() == "Mealie ↔ KitchenOwl Bridge"
