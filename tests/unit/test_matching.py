from bridge.matching import KitchenOwlItem, find_best_match, rank_items


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


def test_rank_items_empty_query_returns_first_candidates_unscored():
    candidates = [
        KitchenOwlItem(id=1, name="Zucchini"),
        KitchenOwlItem(id=2, name="Apple"),
        KitchenOwlItem(id=3, name="Banana"),
    ]
    assert rank_items("", candidates, limit=2) == candidates[:2]


def test_rank_items_ranks_partial_query_above_unrelated_items():
    candidates = [
        KitchenOwlItem(id=1, name="Tomato"),
        KitchenOwlItem(id=2, name="Tomato Sauce"),
        KitchenOwlItem(id=3, name="Banana"),
    ]
    ranked = rank_items("tom", candidates)
    assert ranked[0] in (candidates[0], candidates[1])
    assert candidates[2] not in ranked


def test_rank_items_respects_limit():
    candidates = [KitchenOwlItem(id=i, name=f"Tomato {i}") for i in range(5)]
    assert len(rank_items("tomato", candidates, limit=3)) == 3


def test_rank_items_no_candidates_returns_empty():
    assert rank_items("tomato", []) == []
