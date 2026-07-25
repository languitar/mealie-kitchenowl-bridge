from bridge.matching import KitchenOwlItem, find_best_match


def test_exact_match():
    candidates = [KitchenOwlItem(id=1, name="Banana")]
    assert find_best_match("Banana", candidates) == candidates[0]


def test_plural_matches_singular_item():
    candidates = [KitchenOwlItem(id=1, name="Banana")]
    assert find_best_match("Bananas", candidates) == candidates[0]


def test_minor_spelling_difference_still_matches():
    candidates = [KitchenOwlItem(id=1, name="Tomato")]
    assert find_best_match("Tomatoe", candidates) == candidates[0]


def test_unrelated_ingredient_has_no_match():
    candidates = [KitchenOwlItem(id=1, name="Banana")]
    assert find_best_match("Tomatoes", candidates) is None


def test_no_candidates_has_no_match():
    assert find_best_match("Bananas", []) is None


def test_picks_the_closest_of_multiple_candidates():
    candidates = [KitchenOwlItem(id=1, name="Banana"), KitchenOwlItem(id=2, name="Plantain")]
    assert find_best_match("Bananas", candidates) == candidates[0]
