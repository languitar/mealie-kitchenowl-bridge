from flask import Blueprint, render_template

# Minimal harness page: proves templates/static assets render in a real
# browser (see tests/bdd/features/home_page.feature). Not a real feature.
index_bp = Blueprint("index", __name__)


@index_bp.get("/")
def index():
    return render_template("index.html")
