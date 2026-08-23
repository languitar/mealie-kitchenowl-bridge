from authlib.integrations.flask_client import OAuth
from flask import Flask, current_app, redirect, request, session, url_for

_EXEMPT_BLUEPRINTS = {"auth", "health"}


def _is_exempt() -> bool:
    return request.blueprint in _EXEMPT_BLUEPRINTS or request.endpoint == "static"


def _require_login():
    if _is_exempt() or "user" in session:
        return None
    session["next"] = request.full_path if request.query_string else request.path
    return redirect(url_for("auth.login"))


def register_oidc_client(app: Flask) -> None:
    """Register the OIDC client on this Flask instance only.

    `OAuth(app)` stores its registry on `app.extensions`, keyed per Flask
    instance - avoids the cross-test state leakage a module-level `OAuth()`
    singleton would risk, since the test suite creates a fresh app per test.
    """
    config = app.config["BRIDGE_CONFIG"]
    oauth = OAuth(app)
    client = oauth.register(
        name="oidc",
        server_metadata_url=f"{config.oidc_issuer.rstrip('/')}/.well-known/openid-configuration",
        client_id=config.oidc_client_id,
        client_secret=config.oidc_client_secret,
        client_kwargs={"scope": "openid email profile"},
    )
    app.extensions["oidc_client"] = client


def oidc_client():
    return current_app.extensions["oidc_client"]


def init_auth(app: Flask) -> None:
    from bridge.routes.auth import auth_bp

    app.secret_key = app.config["BRIDGE_CONFIG"].secret_key
    register_oidc_client(app)
    app.register_blueprint(auth_bp)
    app.before_request(_require_login)
