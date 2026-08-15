from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from bridge.auth import init_auth
from bridge.config import Config
from bridge.routes.health import health_bp
from bridge.routes.index import index_bp
from bridge.routes.review import review_bp
from bridge.routes.trigger import trigger_bp


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)
    app.config["BRIDGE_CONFIG"] = config or Config.from_env()
    # Trust the reverse proxy this app is expected to run behind, so
    # url_for(_external=True) (used to build the OIDC redirect_uri) sees the
    # real public scheme/host instead of the proxy's internal one.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    init_auth(app)
    app.register_blueprint(index_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(trigger_bp)
    app.register_blueprint(review_bp)

    return app
