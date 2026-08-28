import pytest
from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from .common import *  # noqa: F401,F403

scenarios("../features/recipe_to_shopping_list.feature")

# htmx adds these classes for the duration of a request/settle/swap cycle - waiting
# for none of them to be present is htmx's own recommended way to know an
# htmx-driven update has fully finished, since the response arriving isn't the same
# moment as htmx finishing applying it to the DOM (bigskysoftware/htmx#2360).
_HTMX_TRANSIENT_CLASSES = ".htmx-request, .htmx-settling, .htmx-swapping, .htmx-added"


def _wait_for_htmx_idle(page):
    expect(page.locator(_HTMX_TRANSIENT_CLASSES)).to_have_count(0)


@pytest.fixture
def config(kitchenowl_config):
    return kitchenowl_config


@given(
    parsers.parse('KitchenOwl has the shopping lists "{first_list}" and "{second_list}"'),
    target_fixture="shopping_lists_by_name",
)
def kitchenowl_has_shopping_lists(kitchenowl_household, first_list, second_list):
    server = kitchenowl_household.server
    return {
        first_list: server.create_shopping_list(kitchenowl_household.id, first_list),
        second_list: server.create_shopping_list(kitchenowl_household.id, second_list),
    }


@given(
    parsers.parse(
        'the shopping list "{list_name}" already has the item "{item_name}" '
        'with quantity "{quantity}"'
    )
)
def shopping_list_already_has_item(
    kitchenowl_household, shopping_lists_by_name, list_name, item_name, quantity
):
    list_id = shopping_lists_by_name[list_name]
    kitchenowl_household.server.add_shopping_list_item(list_id, item_name, quantity)


@pytest.fixture
def kitchenowl_items_by_name() -> dict:
    return {}


@given(
    parsers.parse('KitchenOwl already has an item called "{item_name}"'),
    target_fixture="kitchenowl_items_by_name",
)
def kitchenowl_has_item(kitchenowl_household, kitchenowl_items_by_name, item_name):
    kitchenowl_items_by_name[item_name] = kitchenowl_household.server.create_item(
        kitchenowl_household.id, item_name
    )
    return kitchenowl_items_by_name


@given(parsers.parse('KitchenOwl has no item called "{item_name}"'))
def kitchenowl_has_no_item(kitchenowl_household, item_name):
    items = kitchenowl_household.server.get_items(kitchenowl_household.id)
    assert not any(item["name"].casefold() == item_name.casefold() for item in items)


@then(parsers.parse('I see the shopping lists "{first_list}" and "{second_list}" to choose from'))
def see_shopping_lists(page, first_list, second_list):
    expect(page.get_by_role("button", name=first_list)).to_be_visible()
    expect(page.get_by_role("button", name=second_list)).to_be_visible()


def _ingredient_row(page, ingredient_name: str):
    return page.get_by_role("group", name=ingredient_name)


@given(parsers.parse('I have selected the shopping list "{list_name}"'))
@when(parsers.parse('I select the shopping list "{list_name}"'))
def select_shopping_list(page, list_name):
    # `click()` already waits for the navigation it triggers to complete; the
    # locators/expect() calls in later steps wait for the resulting page's
    # elements themselves, so no need for `networkidle` on top of that.
    page.get_by_role("button", name=list_name).click()


@then(
    parsers.parse(
        'I see the ingredients "{first_ingredient}" and "{second_ingredient}", all pre-selected'
    )
)
def see_ingredients_pre_selected(page, first_ingredient, second_ingredient):
    for ingredient in (first_ingredient, second_ingredient):
        expect(_ingredient_row(page, ingredient).get_by_role("checkbox")).to_be_checked()


def _ingredient_quantity(page, ingredient_name: str):
    return _ingredient_row(page, ingredient_name).get_by_test_id("ingredient-quantity")


@then(parsers.parse('I see the ingredient "{ingredient}" with the quantity "{quantity}"'))
def see_ingredient_quantity(page, ingredient, quantity):
    expect(_ingredient_quantity(page, ingredient)).to_have_text(f"({quantity})")


@then(parsers.parse('I see the ingredient "{ingredient}" with no quantity shown'))
def see_ingredient_no_quantity(page, ingredient):
    expect(_ingredient_quantity(page, ingredient)).not_to_be_attached()


@then(
    parsers.parse(
        'I see the ingredient "{ingredient}" matched to the existing KitchenOwl item "{item_name}"'
    )
)
def see_ingredient_matched(page, kitchenowl_items_by_name, ingredient, item_name):
    expected_item_id = str(kitchenowl_items_by_name[item_name])
    item_choice = _ingredient_row(page, ingredient).get_by_test_id("item-choice")
    expect(item_choice).to_have_value(expected_item_id)


@then(parsers.parse('I see the ingredient "{ingredient}" set to create a new KitchenOwl item'))
def see_ingredient_set_to_create_new(page, ingredient):
    item_choice = _ingredient_row(page, ingredient).get_by_test_id("item-choice")
    expect(item_choice).to_have_value("new")


@when(parsers.parse('I deselect the ingredient "{ingredient}"'))
def deselect_ingredient(page, ingredient):
    _ingredient_row(page, ingredient).get_by_role("checkbox").uncheck()


@when(
    parsers.parse(
        'I select the existing KitchenOwl item "{item_name}" for the ingredient '
        '"{ingredient_name}"'
    ),
)
def select_existing_item_for_ingredient(page, item_name, ingredient_name):
    row = _ingredient_row(page, ingredient_name)
    search_input = row.get_by_role("textbox")
    # A pre-filled search box (from an existing match) fires its own htmx request
    # on focus (no debounce), using the stale value - let that settle before typing
    # the real query, so it can't race with (and overwrite) the one below.
    search_input.click()
    _wait_for_htmx_idle(page)
    search_input.fill(item_name)
    # "input changed" is debounced by 200ms before htmx even starts the request.
    page.wait_for_timeout(250)
    _wait_for_htmx_idle(page)
    suggestion = row.get_by_role("button", name=item_name, exact=True)
    expect(suggestion).to_be_visible()
    suggestion.click()


@when(
    parsers.parse(
        'I choose to create a new KitchenOwl item for the ingredient "{ingredient_name}"'
    ),
)
def choose_new_item_for_ingredient(page, ingredient_name):
    _ingredient_row(page, ingredient_name).get_by_role("textbox").fill("")


@when("I confirm the ingredient selection")
def confirm_ingredient_selection(page):
    # `click()` already waits for a navigation it triggers to complete (i.e. the
    # POST response, and with it the server-side KitchenOwl write, has landed) -
    # no need for `networkidle` on top, which has a mandatory ~500ms settle floor.
    page.get_by_role("button", name="Add to shopping list").click()


def _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name) -> dict:
    list_id = shopping_lists_by_name[list_name]
    items = kitchenowl_household.server.get_shopping_list_items(kitchenowl_household.id, list_id)
    return {item["name"]: item for item in items}


@then(
    parsers.parse(
        'the ingredients "{first_ingredient}" and "{second_ingredient}" are added to the '
        '"{list_name}" shopping list in KitchenOwl'
    )
)
def ingredients_added_to_shopping_list(
    kitchenowl_household,
    shopping_lists_by_name,
    list_name,
    first_ingredient,
    second_ingredient,
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items.keys() == {first_ingredient, second_ingredient}


@then("I am redirected to the shopping list in KitchenOwl")
def redirected_to_kitchenowl_shopping_list(page, kitchenowl_household):
    """KitchenOwl's frontend has no deep link to a specific list (see
    `push_to_shopping_list`), so this only checks the general per-household items
    page - checked right as the browser lands there, before KitchenOwl's own
    frontend has bootstrapped enough to client-side redirect an unauthenticated
    browser onward to its login page.
    """
    expect(page).to_have_url(
        f"{kitchenowl_household.server.base_url}/household/{kitchenowl_household.id}/items"
    )


@then(
    parsers.parse(
        'only the ingredient "{ingredient}" is added to the "{list_name}" shopping list '
        "in KitchenOwl"
    )
)
def only_ingredient_added_to_shopping_list(
    kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items.keys() == {ingredient}


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        'with the description "{description}"'
    )
)
def ingredient_added_with_description(
    kitchenowl_household, shopping_lists_by_name, list_name, ingredient, description
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert items[ingredient]["description"] == description


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        "with no description"
    )
)
def ingredient_added_without_description(
    kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert not items[ingredient].get("description")


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        'as the existing item "{item_name}"'
    )
)
def ingredient_added_as_existing_item(
    kitchenowl_household,
    shopping_lists_by_name,
    kitchenowl_items_by_name,
    list_name,
    ingredient,
    item_name,
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert ingredient not in items
    assert items[item_name]["id"] == kitchenowl_items_by_name[item_name]


@then(
    parsers.parse(
        'the ingredient "{ingredient}" is added to the "{list_name}" shopping list in KitchenOwl '
        "as a new item"
    )
)
def ingredient_added_as_new_item(
    kitchenowl_household, shopping_lists_by_name, list_name, ingredient
):
    items = _shopping_list_items_by_name(kitchenowl_household, shopping_lists_by_name, list_name)
    assert ingredient in items


@when(
    # `parsers.parse`'s default field type requires at least one character, which
    # can't match the empty-query scenario's "" - a plain regex allows it. This
    # matches Gherkin step text, not HTML, so it's unrelated to locator strategy.
    parsers.re(r'I search the existing KitchenOwl items for "(?P<query>.*)"'),
)
def search_existing_items(page, query):
    page.get_by_role("textbox").fill(query)
    # "input changed" is debounced by 200ms before htmx even starts the request.
    # Settling here (rather than relying on the assertions below to retry) matters
    # for the "not suggested"/"no items suggested" checks: an assertion that a
    # button never appears would otherwise trivially pass before the search has
    # even happened.
    page.wait_for_timeout(250)
    _wait_for_htmx_idle(page)


@then(parsers.parse('I see the KitchenOwl items "{first_item}" and "{second_item}" suggested'))
def see_items_suggested(page, first_item, second_item):
    expect(page.get_by_role("button", name=first_item, exact=True)).to_be_visible()
    expect(page.get_by_role("button", name=second_item, exact=True)).to_be_visible()


@then(parsers.parse('I see the KitchenOwl item "{item_name}" suggested'))
def see_item_suggested(page, item_name):
    expect(page.get_by_role("button", name=item_name, exact=True)).to_be_visible()


@then(parsers.parse('I do not see the KitchenOwl item "{item_name}" suggested'))
def do_not_see_item_suggested(page, item_name):
    expect(page.get_by_role("button", name=item_name, exact=True)).not_to_be_visible()


@then("I see no KitchenOwl items suggested")
def see_no_items_suggested(page):
    expect(page.get_by_text("No matching items")).to_be_visible()
