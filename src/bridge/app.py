from flask import Flask

from bridge.config import Config
from bridge.routes.health import health_bp
from bridge.routes.index import index_bp
from bridge.routes.review import review_bp
from bridge.routes.webhook import webhook_bp


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)
    app.config["BRIDGE_CONFIG"] = config or Config.from_env()

    app.register_blueprint(index_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(review_bp)

    return app
