from dataclasses import dataclass

import simplemma
from rapidfuzz import fuzz

_LEMMATIZE_LANGUAGES = ("en",)
_MATCH_THRESHOLD = 80


@dataclass(frozen=True)
class KitchenOwlItem:
    id: int
    name: str


def _normalize(text: str) -> str:
    return " ".join(
        simplemma.lemmatize(word, lang=_LEMMATIZE_LANGUAGES) for word in text.casefold().split()
    )


def find_best_match(
    ingredient_name: str, candidates: list[KitchenOwlItem]
) -> KitchenOwlItem | None:
    """Suggest an existing KitchenOwl item matching a Mealie ingredient's name.

    Names are lemmatized first (so "bananas" normalizes the same as "banana")
    before scoring similarity, to tolerate plural/inflected forms as well as
    minor spelling differences - not just exact-name matches.
    """
    normalized_ingredient = _normalize(ingredient_name)

    best_candidate: KitchenOwlItem | None = None
    best_score = 0.0
    for candidate in candidates:
        score = fuzz.ratio(normalized_ingredient, _normalize(candidate.name))
        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_score >= _MATCH_THRESHOLD:
        return best_candidate
    return None


def rank_items(
    query: str, candidates: list[KitchenOwlItem], limit: int = 8
) -> list[KitchenOwlItem]:
    """Rank existing KitchenOwl items by fuzzy similarity to a free-text search query.

    Used for search-as-you-type, unlike `find_best_match`'s one-shot
    best-guess match against a full ingredient name. An empty query (the
    user has focused the field but not typed anything yet) returns the
    first `limit` candidates unscored, so the field still offers a
    browsable list rather than nothing. `WRatio` tolerates the query being
    a partial/shorter prefix of a candidate's name better than the plain
    `ratio` used by `find_best_match`, which expects two comparable full
    names.
    """
    if not query:
        return candidates[:limit]

    normalized_query = _normalize(query)
    scored = [
        (fuzz.WRatio(normalized_query, _normalize(candidate.name)), candidate)
        for candidate in candidates
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [candidate for score, candidate in scored[:limit] if score > 0]
