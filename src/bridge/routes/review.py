from flask import Blueprint

# Reserved for the HTMX ingredient review/edit screen shown before pushing
# items onto a KitchenOwl shopping list. No routes are registered yet;
# see AGENTS.md for the workflow to add this as a real feature.
review_bp = Blueprint("review", __name__)
