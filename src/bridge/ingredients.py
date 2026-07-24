from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    name: str
    quantity: str | None = None


def parse_ingredient(raw: dict) -> Ingredient:
    """Split a Mealie `recipeIngredient` entry into a KitchenOwl item name and quantity.

    Mealie's `display` field bundles quantity, unit, food and note into one
    formatted string, but KitchenOwl wants the food name as the item's name
    and the quantity (with its unit, if any) as a separate description - so
    this reads the underlying structured `food`/`quantity`/`unit` fields
    instead of parsing `display`. Falls back to `display` as the name when
    there's no structured `food` (e.g. free-text ingredients).
    """
    food = raw.get("food") or {}
    name = food.get("name") or raw["display"]

    quantity_value = raw.get("quantity")
    if quantity_value is None:
        return Ingredient(name=name)

    quantity = f"{quantity_value:g}"
    unit_name = (raw.get("unit") or {}).get("name")
    if unit_name:
        quantity = f"{quantity} {unit_name}"

    return Ingredient(name=name, quantity=quantity)
