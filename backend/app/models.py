import uuid

from .extensions import db
from .utils.time import now_ms


def gen_id():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, default='')
    level = db.Column(db.String, nullable=True)
    notifications = db.Column(db.Integer, default=0)
    password_hash = db.Column(db.String, nullable=False)
    api_key_encrypted = db.Column(db.String, nullable=True)
    broker_key_encrypted = db.Column(db.String, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)


class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    returns = db.Column(db.Float, default=0)
    win_rate = db.Column(db.Float, default=0)
    max_drawdown = db.Column(db.Float, default=0)
    tags = db.Column(db.JSON, default=list)
    last_update = db.Column(db.BigInteger, default=now_ms)
    trades = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)


class StrategyVersion(db.Model):
    __tablename__ = 'strategy_versions'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'))
    version = db.Column(db.String, nullable=False)
    file_id = db.Column(db.String, db.ForeignKey('files.id'))
    checksum = db.Column(db.String, nullable=True)
    created_at = db.Column(db.BigInteger, default=now_ms)


class Backtest(db.Model):
    __tablename__ = 'backtests'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    started_at = db.Column(db.BigInteger, nullable=False)
    finished_at = db.Column(db.BigInteger, nullable=True)
    summary = db.Column(db.JSON, nullable=True)
    job_id = db.Column(db.String, nullable=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    created_at = db.Column(db.BigInteger, default=now_ms)
    updated_at = db.Column(db.BigInteger, default=now_ms)


class BacktestTrade(db.Model):
    __tablename__ = 'backtest_trades'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    backtest_id = db.Column(db.String, db.ForeignKey('backtests.id'))
    symbol = db.Column(db.String, nullable=False)
    side = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    pnl = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)


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
