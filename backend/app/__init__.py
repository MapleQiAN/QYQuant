from flask import Flask

from . import models  # noqa: F401
from .blueprints.auth import bp as auth_bp
from .blueprints.admin import bp as admin_bp
from .blueprints.backtests import bp as backtests_bp
from .blueprints.bots import bp as bots_bp
from .blueprints.community import bp as community_bp
from .blueprints.dashboard import bp as dashboard_bp
from .blueprints.files import bp as files_bp
from .blueprints.forum import bp as forum_bp
from .blueprints.health import bp as health_bp
from .blueprints.integrations import bp as integrations_bp
from .blueprints.marketplace import bp as marketplace_bp
from .blueprints.notifications import bp as notifications_bp
from .blueprints.payments import bp as payments_bp
from .blueprints.presets import bp as presets_bp
from .blueprints.reports import bp as reports_bp
from .blueprints.simulation import bp as simulation_bp
from .blueprints.users import bp as users_bp
from .config import get_config
from .errors import register_error_handlers
from .extensions import api, cors, db, jwt, mail, migrate
from .models import User
from .utils.redis_client import get_auth_store
from .utils.response import error_response
from .utils.request_id import register_request_id

try:
    from .blueprints.strategies import bp as strategies_bp
except ModuleNotFoundError:  # pragma: no cover - optional until blueprint source is restored
    strategies_bp = None


def create_app(env=None):
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    register_request_id(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    app.config.setdefault('API_TITLE', 'QYQuant API')
    app.config.setdefault('API_VERSION', 'v1')
    app.config.setdefault('OPENAPI_VERSION', '3.0.3')
    app.config.setdefault('OPENAPI_URL_PREFIX', '/api')
    app.config.setdefault('OPENAPI_SWAGGER_UI_PATH', '/docs')
    app.config.setdefault('OPENAPI_SWAGGER_UI_URL', 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/')

    api.init_app(app)
    _register_jwt_callbacks()

    register_error_handlers(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dashboard_bp)
    if strategies_bp is not None:
        app.register_blueprint(strategies_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(presets_bp)
    app.register_blueprint(backtests_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(bots_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(payments_bp)

    return app


def _register_jwt_callbacks():
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_payload):
        user = db.session.get(User, jwt_payload["sub"])
        if user is None or user.deleted_at is not None:
            return None
        return user

    @jwt.user_lookup_error_loader
    def user_lookup_error(_jwt_header, _jwt_payload):
        return error_response("UNAUTHORIZED", "未登录", 401)

    @jwt.token_in_blocklist_loader
    def token_in_blocklist(jwt_header, jwt_payload):
        return get_auth_store().is_token_blacklisted(jwt_payload["jti"])

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response("TOKEN_EXPIRED", "登录已过期，请重新登录", 401)

    @jwt.unauthorized_loader
    def unauthorized(message):
        return error_response("UNAUTHORIZED", "未登录", 401)

    @jwt.invalid_token_loader
    def invalid_token(message):
        return error_response("INVALID_TOKEN", "无效的访问令牌", 401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return error_response("TOKEN_REVOKED", "登录已失效，请重新登录", 401)
