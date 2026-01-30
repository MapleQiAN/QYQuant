from flask import Flask

from . import models  # noqa: F401
from .blueprints.auth import bp as auth_bp
from .blueprints.backtests import bp as backtests_bp
from .blueprints.bots import bp as bots_bp
from .blueprints.files import bp as files_bp
from .blueprints.forum import bp as forum_bp
from .blueprints.health import bp as health_bp
from .blueprints.strategies import bp as strategies_bp
from .blueprints.users import bp as users_bp
from .config import get_config
from .errors import register_error_handlers
from .extensions import api, cors, db, jwt, migrate
from .utils.request_id import register_request_id


def create_app(env=None):
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    register_request_id(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.config.setdefault('API_TITLE', 'QYQuant API')
    app.config.setdefault('API_VERSION', 'v1')
    app.config.setdefault('OPENAPI_VERSION', '3.0.3')
    app.config.setdefault('OPENAPI_URL_PREFIX', '/api')
    app.config.setdefault('OPENAPI_SWAGGER_UI_PATH', '/docs')
    app.config.setdefault('OPENAPI_SWAGGER_UI_URL', 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/')

    api.init_app(app)

    register_error_handlers(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(backtests_bp)
    app.register_blueprint(bots_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(files_bp)

    return app
