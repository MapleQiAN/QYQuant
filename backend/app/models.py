import uuid
from enum import Enum

from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from .extensions import db
from .utils.time import now_ms, now_utc


def gen_id():
    return str(uuid.uuid4())


job_json_type = JSON().with_variant(JSONB(astext_type=Text()), 'postgresql')
search_vector_type = Text().with_variant(TSVECTOR(), 'postgresql')


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
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    nickname = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String, nullable=False, default='')
    bio = db.Column(db.String(200), nullable=False, default='')
    role = db.Column(db.String(32), nullable=False, default='user')
    plan_level = db.Column(db.String(32), nullable=False, default='free')
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    sim_disclaimer_accepted = db.Column(db.Boolean, nullable=False, default=False)
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


class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = (
        db.Index('ix_notifications_user_id', 'user_id'),
        db.Index('ix_notifications_created_at', 'created_at'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class Report(db.Model):
    __tablename__ = 'reports'
    __table_args__ = (
        db.Index('ix_reports_reporter_strategy', 'reporter_id', 'strategy_id'),
        db.Index('ix_reports_status', 'status'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    reporter_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reviewed_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)


class Strategy(db.Model):
    __tablename__ = 'strategies'
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'source_strategy_id', name='uq_user_imported_strategy'),
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
    source_strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    review_status = db.Column(db.String(32), nullable=False, default='pending')
    display_metrics = db.Column(job_json_type, nullable=True, default=dict)
    title_tsv = db.Column(search_vector_type, nullable=True)
    description_tsv = db.Column(search_vector_type, nullable=True)
    returns = db.Column(db.Float, default=0)
    win_rate = db.Column(db.Float, default=0)
    max_drawdown = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    last_update = db.Column(db.BigInteger, default=now_ms)
    trades = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    storage_key = db.Column(db.String, nullable=True)
    original_source_file_id = db.Column(db.String, db.ForeignKey('files.id'), nullable=True)
    built_package_file_id = db.Column(db.String, db.ForeignKey('files.id'), nullable=True)
    code_encrypted = db.Column(db.LargeBinary, nullable=True)
    code_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

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


class StrategyImportDraft(db.Model):
    __tablename__ = 'strategy_import_drafts'
    __table_args__ = (
        db.Index('ix_strategy_import_drafts_owner_status', 'owner_id', 'status'),
        db.Index('ix_strategy_import_drafts_expires_at', 'expires_at'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    source_file_id = db.Column(db.String, db.ForeignKey('files.id'), nullable=False)
    source_type = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='analyzed')
    analysis_payload = db.Column(job_json_type, nullable=False, default=dict)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


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


class DataSourceHealthStatus(db.Model):
    __tablename__ = 'data_source_health_status'

    source_name = db.Column(db.String(50), primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='unknown')
    last_checked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_success_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_failure_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_error_message = db.Column(db.Text, nullable=True)
    consecutive_failures = db.Column(db.Integer, nullable=False, default=0)
    last_notified_status = db.Column(db.String(20), nullable=True)


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


class SimulationBot(db.Model):
    __tablename__ = 'simulation_bots'
    __table_args__ = (
        db.Index('idx_simulation_bots_user_id', 'user_id'),
        db.Index('idx_simulation_bots_status', 'status'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=False)
    initial_capital = db.Column(db.Numeric(18, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active', server_default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, server_default=db.func.now())
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)


class SimulationRecord(db.Model):
    __tablename__ = 'simulation_records'
    __table_args__ = (
        db.Index('idx_simulation_records_bot_id', 'bot_id'),
        db.Index('idx_simulation_records_trade_date', 'bot_id', 'trade_date'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    equity = db.Column(db.Numeric(18, 2), nullable=False)
    cash = db.Column(db.Numeric(18, 2), nullable=False)
    daily_return = db.Column(db.Numeric(10, 6), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, server_default=db.func.now())


class SimulationPosition(db.Model):
    __tablename__ = 'simulation_positions'
    __table_args__ = (
        db.PrimaryKeyConstraint('bot_id', 'symbol'),
    )

    bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    avg_cost = db.Column(db.Numeric(18, 4), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc, server_default=db.func.now())


class SimulationTrade(db.Model):
    __tablename__ = 'simulation_trades'
    __table_args__ = (
        db.Index('idx_simulation_trades_bot_id', 'bot_id'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(4), nullable=False)
    price = db.Column(db.Numeric(18, 4), nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, server_default=db.func.now())


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
    content = db.Column(db.Text, nullable=True)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=True)
    likes_count = db.Column(db.Integer, nullable=False, default=0)
    comments_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=True, default=now_utc)


class PostInteraction(db.Model):
    __tablename__ = 'post_interactions'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', 'type', name='uq_post_interactions_user_post_type'),
        db.Index('ix_post_interactions_user_id', 'user_id'),
        db.Index('ix_post_interactions_post_id', 'post_id'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.String, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class PostComment(db.Model):
    __tablename__ = 'post_comments'
    __table_args__ = (
        db.Index('ix_post_comments_post_id', 'post_id'),
        db.Index('ix_post_comments_created_at', 'created_at'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    post_id = db.Column(db.String, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


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


class PaymentOrder(db.Model):
    __tablename__ = 'payment_orders'

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    plan_level = db.Column(db.String(32), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    provider_order_id = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    pay_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    plan_level = db.Column(db.String(32), nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    payment_provider = db.Column(db.String(20), nullable=False)
    payment_order_id = db.Column(db.String, db.ForeignKey('payment_orders.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
