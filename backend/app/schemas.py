from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.Str()
    email = fields.Str()
    name = fields.Str(required=True)
    avatar = fields.Str(required=True)
    level = fields.Str(allow_none=True)
    notifications = fields.Int(allow_none=True)


class StrategySchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)
    symbol = fields.Str(required=True)
    status = fields.Str(required=True)
    returns = fields.Float()
    winRate = fields.Float(attribute='win_rate')
    maxDrawdown = fields.Float(attribute='max_drawdown')
    tags = fields.List(fields.Str())
    lastUpdate = fields.Int(attribute='last_update')
    trades = fields.Int()


class BacktestSummarySchema(Schema):
    totalReturn = fields.Float()
    annualizedReturn = fields.Float(allow_none=True)
    sharpeRatio = fields.Float(allow_none=True)
    maxDrawdown = fields.Float(allow_none=True)
    winRate = fields.Float(allow_none=True)
    profitFactor = fields.Float(allow_none=True)
    totalTrades = fields.Int(allow_none=True)
    avgHoldingDays = fields.Float(allow_none=True)


class KlineBarSchema(Schema):
    time = fields.Int()
    open = fields.Float()
    high = fields.Float()
    low = fields.Float()
    close = fields.Float()
    volume = fields.Float()


class BacktestTradeSchema(Schema):
    id = fields.Str()
    symbol = fields.Str()
    side = fields.Str()
    price = fields.Float()
    quantity = fields.Float()
    pnl = fields.Float(allow_none=True)
    timestamp = fields.Int()


class BacktestSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    symbol = fields.Str()
    status = fields.Str()
    startedAt = fields.Int(attribute='started_at')
    finishedAt = fields.Int(attribute='finished_at', allow_none=True)
    summary = fields.Nested(BacktestSummarySchema, allow_none=True)


class BotSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    strategy = fields.Str()
    status = fields.Str()
    profit = fields.Float()
    runtime = fields.Str()
    capital = fields.Float()
    tags = fields.List(fields.Str())
    paper = fields.Bool()


class OrderSchema(Schema):
    id = fields.Str()
    symbol = fields.Str()
    side = fields.Str()
    price = fields.Float()
    quantity = fields.Float()
    status = fields.Str()
    pnl = fields.Float(allow_none=True)
    timestamp = fields.Int()


class PostSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Str()
    avatar = fields.Str()
    likes = fields.Int()
    comments = fields.Int()
    timestamp = fields.Int()
    tags = fields.List(fields.Str())


class CommentSchema(Schema):
    id = fields.Str()
    author = fields.Str()
    avatar = fields.Str()
    content = fields.Str()
    timestamp = fields.Int()


class FileSchema(Schema):
    id = fields.Str()
    filename = fields.Str()
    contentType = fields.Str(attribute='content_type')
    size = fields.Int()
    path = fields.Str()


class FollowSchema(Schema):
    id = fields.Str()
    followerId = fields.Str(attribute='follower_id')
    followingId = fields.Str(attribute='following_id')
    createdAt = fields.Int(attribute='created_at')
