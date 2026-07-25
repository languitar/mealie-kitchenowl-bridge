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
