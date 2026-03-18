import uuid
from enum import Enum

from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import JSONB

from .extensions import db
from .utils.time import now_ms, now_utc


def gen_id():
    return str(uuid.uuid4())


job_json_type = JSON().with_variant(JSONB(astext_type=Text()), 'postgresql')


class BacktestJobStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    TIMEOUT = 'timeout'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    nickname = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String, nullable=False, default='')
    bio = db.Column(db.String(200), nullable=False, default='')
    role = db.Column(db.String(32), nullable=False, default='user')
    plan_level = db.Column(db.String(32), nullable=False, default='free')
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    jti = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    operator_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.String, nullable=False)
    details = db.Column(db.JSON, nullable=True, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class Strategy(db.Model):
    __tablename__ = 'strategies'
    __table_args__ = (
        db.Index('ix_strategies_category', 'category'),
        db.Index(
            'ix_strategies_marketplace_public_verified',
            'is_public',
            'is_verified',
            postgresql_where=db.text('is_public = true'),
            sqlite_where=db.text('is_public = 1'),
        ),
        db.Index(
            'ix_strategies_marketplace_featured',
            'is_featured',
            postgresql_where=db.text('is_featured = true'),
            sqlite_where=db.text('is_featured = 1'),
        ),
    )
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=True)
    symbol = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(64), nullable=True)
    source = db.Column(db.String(32), nullable=False, default='upload')
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    review_status = db.Column(db.String(32), nullable=False, default='pending')
    display_metrics = db.Column(db.JSON, nullable=False, default=dict)
    returns = db.Column(db.Float, default=0)
    win_rate = db.Column(db.Float, default=0)
    max_drawdown = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    last_update = db.Column(db.BigInteger, default=now_ms)
    trades = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    review_status = db.Column(db.String(32), nullable=False, default='pending')
    display_metrics = db.Column(job_json_type, nullable=True, default=dict)
    storage_key = db.Column(db.String, nullable=True)
    code_encrypted = db.Column(db.LargeBinary, nullable=True)
    code_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)

    def to_card_dict(self, *, author=None):
        author_payload = {
            "nickname": getattr(author, "nickname", ""),
            "avatar_url": getattr(author, "avatar_url", ""),
        }
        tags = self.tags if isinstance(self.tags, list) else []
        metrics = self.display_metrics if isinstance(self.display_metrics, dict) else {}

        return {
            "id": self.id,
            "title": self.title or self.name,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": [str(tag) for tag in tags],
            "is_verified": bool(self.is_verified),
            "display_metrics": metrics,
            "author": author_payload,
        }


class StrategyVersion(db.Model):
    __tablename__ = 'strategy_versions'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'))
    version = db.Column(db.String, nullable=False)
    file_id = db.Column(db.String, db.ForeignKey('files.id'))
    checksum = db.Column(db.String, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)


class StrategyParameterPreset(db.Model):
    __tablename__ = 'strategy_parameter_presets'
    __table_args__ = (
        db.Index('ix_strategy_parameter_presets_strategy_user', 'strategy_id', 'user_id'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parameters = db.Column(job_json_type, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class BacktestJob(db.Model):
    __tablename__ = 'backtest_jobs'
    __table_args__ = (
        db.Index('ix_backtest_jobs_user_id_created_at', 'user_id', 'created_at'),
        db.Index('ix_backtest_jobs_status', 'status'),
        db.Index('ix_backtest_jobs_strategy_id', 'strategy_id'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=True)
    status = db.Column(
        db.Enum(
            BacktestJobStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            validate_strings=True,
            name='backtest_job_status',
        ),
        nullable=False,
        default=BacktestJobStatus.PENDING.value,
    )
    params = db.Column(job_json_type, nullable=False, default=dict)
    result_summary = db.Column(job_json_type, nullable=True)
    result_storage_key = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class BacktestTrade(db.Model):
    __tablename__ = 'backtest_trades'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    backtest_id = db.Column(db.String, db.ForeignKey('backtest_jobs.id'))
    symbol = db.Column(db.String, nullable=False)
    side = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    pnl = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)


class UserQuota(db.Model):
    __tablename__ = 'user_quota'

    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    plan_level = db.Column(db.String(32), nullable=False, default='free')
    used_count = db.Column(db.Integer, nullable=False, default=0)
    reset_at = db.Column(db.DateTime(timezone=True), nullable=True)


class MarketDataCache(db.Model):
    __tablename__ = 'market_data_cache'
    __table_args__ = (
        db.Index('ix_market_data_cache_symbol_trade_date_desc', 'symbol', db.text('trade_date DESC')),
    )

    symbol = db.Column(db.String(20), primary_key=True)
    trade_date = db.Column(db.Date, primary_key=True)
    open = db.Column(db.Numeric(18, 6), nullable=False)
    high = db.Column(db.Numeric(18, 6), nullable=False)
    low = db.Column(db.Numeric(18, 6), nullable=False)
    close = db.Column(db.Numeric(18, 6), nullable=False)
    volume = db.Column(db.BigInteger, nullable=False)
    source = db.Column(db.String(20), nullable=False, default='joinquant', server_default='joinquant')
    cached_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, server_default=db.func.now())


class BotInstance(db.Model):
    __tablename__ = 'bot_instances'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    strategy = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    profit = db.Column(db.Float, default=0)
    runtime = db.Column(db.String, default='0d')
    capital = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    paper = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    bot_id = db.Column(db.String, db.ForeignKey('bot_instances.id'))
    symbol = db.Column(db.String, nullable=False)
    side = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, default='filled')
    pnl = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)
    client_order_id = db.Column(db.String, unique=True, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.BigInteger, nullable=False)
    tags = db.Column(db.JSON, default=list)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    author = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)


class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)


class Tip(db.Model):
    __tablename__ = 'tips'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'))
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String, nullable=False, default='USD')
    created_at = db.Column(db.BigInteger, default=now_ms)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    filename = db.Column(db.String, nullable=False)
    content_type = db.Column(db.String, nullable=False)
    size = db.Column(db.Integer, nullable=False)
    path = db.Column(db.String, nullable=False)
    created_at = db.Column(db.BigInteger, default=now_ms)


class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    follower_id = db.Column(db.String, db.ForeignKey('users.id'))
    following_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
