from marshmallow import Schema, fields, validate

from .utils.phone import mask_phone
from .utils.time import format_beijing_iso


def _value(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


class UserPrivateSchema(Schema):
    id = fields.Str()
    phone = fields.Function(lambda obj: mask_phone(_value(obj, "phone")))
    nickname = fields.Str(required=True)
    avatar_url = fields.Str(required=True)
    bio = fields.Str(required=True)
    role = fields.Str(required=True)
    plan_level = fields.Str(required=True)
    is_banned = fields.Bool(required=True)
    onboarding_completed = fields.Bool(required=True)
    created_at = fields.Function(lambda obj: format_beijing_iso(_value(obj, "created_at")))
    updated_at = fields.Function(lambda obj: format_beijing_iso(_value(obj, "updated_at")))


class UserPublicSchema(Schema):
    id = fields.Str()
    nickname = fields.Str(required=True)
    avatar_url = fields.Str(required=True)
    bio = fields.Str(required=True)
    is_banned = fields.Bool(required=True)
    created_at = fields.Function(lambda obj: format_beijing_iso(_value(obj, "created_at")))


class UserUpdateSchema(Schema):
    nickname = fields.Str(validate=validate.Length(min=2, max=30))
    bio = fields.Str(validate=validate.Length(max=200))
    avatar_url = fields.Str()


class UserSchema(UserPrivateSchema):
    pass


class StrategySchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)
    title = fields.Str(allow_none=True)
    symbol = fields.Str(required=True)
    status = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    category = fields.Str(allow_none=True)
    source = fields.Function(lambda obj: _value(obj, "source") or "upload")
    reviewStatus = fields.Str(attribute='review_status')
    isPublic = fields.Bool(attribute='is_public')
    returns = fields.Float()
    winRate = fields.Float(attribute='win_rate')
    maxDrawdown = fields.Float(attribute='max_drawdown')
    tags = fields.List(fields.Str())
    lastUpdate = fields.Int(attribute='last_update')
    trades = fields.Int()
    createdAt = fields.Int(attribute='created_at')


class StrategyParameterSchema(Schema):
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    default = fields.Raw(allow_none=True)
    required = fields.Bool(required=True)
    min = fields.Float(allow_none=True)
    max = fields.Float(allow_none=True)
    step = fields.Float(allow_none=True)
    description = fields.Str(allow_none=True)
    options = fields.List(fields.Raw(), allow_none=True)


class StrategyParameterPresetSchema(Schema):
    id = fields.Str()
    strategyId = fields.Str(attribute='strategy_id')
    userId = fields.Str(attribute='user_id')
    name = fields.Str(required=True)
    parameters = fields.Dict(required=True)
    createdAt = fields.Function(lambda obj: format_beijing_iso(_value(obj, "created_at")))


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
    status = fields.Str()
    userId = fields.Str(attribute='user_id', allow_none=True)
    strategyId = fields.Str(attribute='strategy_id', allow_none=True)
    params = fields.Dict(allow_none=True)
    resultSummary = fields.Dict(attribute='result_summary', allow_none=True)
    resultStorageKey = fields.Str(attribute='result_storage_key', allow_none=True)
    errorMessage = fields.Str(attribute='error_message', allow_none=True)
    startedAt = fields.Function(lambda obj: format_beijing_iso(_value(obj, "started_at")))
    completedAt = fields.Function(lambda obj: format_beijing_iso(_value(obj, "completed_at")))
    createdAt = fields.Function(lambda obj: format_beijing_iso(_value(obj, "created_at")))


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
