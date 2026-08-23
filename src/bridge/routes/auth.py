from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, redirect, session, url_for

from bridge.auth import oidc_client
from bridge.errors import render_error

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login():
    return oidc_client().authorize_redirect(url_for("auth.callback", _external=True))


@auth_bp.get("/callback")
def callback():
    try:
        token = oidc_client().authorize_access_token()
    except OAuthError:
        return render_error("Login failed.", 401)

    userinfo = token.get("userinfo") or {}
    session["user"] = {"sub": userinfo.get("sub"), "email": userinfo.get("email")}
    return redirect(session.pop("next", None) or url_for("index.index"))


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index.index"))
