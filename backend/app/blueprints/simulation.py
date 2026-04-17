import json
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from flask import Response, request, stream_with_context
from flask_jwt_extended import decode_token, get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import SimulationBot, SimulationPosition, SimulationRecord, SimulationTrade, Strategy, User
from ..quota import get_bot_slot_limit
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso, now_utc

bp = Blueprint('simulation', __name__, url_prefix='/api/v1/simulation')

ACTIVE_STATUSES = {'active'}


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response('USER_NOT_FOUND', 'user not found', 404)
    return user, None


def _get_bot_for_user(bot_id: str, user_id: str):
    return SimulationBot.query.filter(
        SimulationBot.id == bot_id,
        SimulationBot.user_id == user_id,
        SimulationBot.deleted_at.is_(None),
    ).first()


def _serialize_record(record: SimulationRecord):
    return {
        'trade_date': str(record.trade_date),
        'equity': f'{record.equity:.2f}',
        'cash': f'{record.cash:.2f}',
        'daily_return': f'{record.daily_return:.6f}',
    }


def _serialize_position(position: SimulationPosition):
    return {
        'symbol': position.symbol,
        'quantity': f'{position.quantity:.4f}',
        'avg_cost': f'{position.avg_cost:.4f}',
        'updated_at': format_beijing_iso(position.updated_at),
    }


def _serialize_trade(trade: SimulationTrade):
    return {
        'trade_date': str(trade.trade_date),
        'symbol': trade.symbol,
        'side': trade.side,
        'price': f'{trade.price:.4f}',
        'quantity': f'{trade.quantity:.4f}',
    }


def _build_bot_snapshot(bot_id: str):
    records = (
        SimulationRecord.query
        .filter_by(bot_id=bot_id)
        .order_by(SimulationRecord.trade_date.asc())
        .all()
    )
    positions = (
        SimulationPosition.query
        .filter_by(bot_id=bot_id)
        .order_by(SimulationPosition.symbol.asc())
        .all()
    )

    serialized_records = [_serialize_record(record) for record in records]
    return {
        'records': [
            {
                'trade_date': record['trade_date'],
                'equity': record['equity'],
                'daily_return': record['daily_return'],
            }
            for record in serialized_records
        ],
        'positions': [
            {
                'symbol': position.symbol,
                'quantity': f'{position.quantity:.4f}',
                'avg_cost': f'{position.avg_cost:.4f}',
            }
            for position in positions
        ],
    }


def _snapshot_version(bot_id: str):
    latest_record_date = (
        db.session.query(db.func.max(SimulationRecord.trade_date))
        .filter(SimulationRecord.bot_id == bot_id)
        .scalar()
    )
    latest_position_update = (
        db.session.query(db.func.max(SimulationPosition.updated_at))
        .filter(SimulationPosition.bot_id == bot_id)
        .scalar()
    )
    return (
        latest_record_date.isoformat() if latest_record_date else '',
        latest_position_update.isoformat() if latest_position_update else '',
    )


def _resolve_stream_user_id():
    token = request.args.get('token', '')
    if not token:
        return None, error_response('UNAUTHORIZED', 'Missing token', 401)

    try:
        decoded = decode_token(token)
    except Exception:
        return None, error_response('UNAUTHORIZED', 'Invalid token', 401)

    user_id = decoded.get('sub')
    if not user_id:
        return None, error_response('UNAUTHORIZED', 'Invalid token', 401)

    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response('UNAUTHORIZED', 'Invalid token', 401)

    return user_id, None


@bp.post('/disclaimer/accept')
@jwt_required()
def accept_disclaimer():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    if not user.sim_disclaimer_accepted:
        user.sim_disclaimer_accepted = True
        db.session.commit()

    return ok({'sim_disclaimer_accepted': True})


@bp.post('/bots')
@jwt_required()
def create_bot():
    user_id = get_jwt_identity()
    user, error = _get_user_or_404(user_id)
    if error:
        return error

    payload = request.get_json() or {}
    strategy_id = payload.get('strategy_id')
    initial_capital = payload.get('initial_capital')

    strategy = Strategy.query.filter_by(id=strategy_id, owner_id=user_id).first()
    if strategy is None:
        return error_response('STRATEGY_NOT_FOUND', 'Strategy not found', 404)

    try:
        capital = Decimal(str(initial_capital))
    except (InvalidOperation, TypeError, ValueError):
        return error_response('VALIDATION_ERROR', 'initial_capital must be numeric', 422)

    if capital < 1000:
        return error_response('VALIDATION_ERROR', 'initial_capital must be at least 1000', 422)

    slot_limit = get_bot_slot_limit(user.plan_level)
    active_count = (
        SimulationBot.query
        .filter(
            SimulationBot.user_id == user_id,
            SimulationBot.status.in_(ACTIVE_STATUSES),
            SimulationBot.deleted_at.is_(None),
        )
        .count()
    )
    if active_count >= slot_limit:
        return error_response(
            'SIMULATION_SLOT_LIMIT_REACHED',
            f'Current plan supports at most {slot_limit} active simulation bots',
            403,
        )

    bot = SimulationBot(
        user_id=user_id,
        strategy_id=strategy_id,
        initial_capital=capital,
        status='active',
    )
    db.session.add(bot)
    db.session.commit()

    return ok({
        'id': bot.id,
        'strategy_id': bot.strategy_id,
        'initial_capital': f'{bot.initial_capital:.2f}',
        'status': bot.status,
        'created_at': format_beijing_iso(bot.created_at),
    }), 201


@bp.get('/bots')
@jwt_required()
def list_bots():
    user_id = get_jwt_identity()
    bots = (
        SimulationBot.query
        .filter(
            SimulationBot.user_id == user_id,
            SimulationBot.deleted_at.is_(None),
        )
        .order_by(SimulationBot.created_at.desc())
        .all()
    )

    strategy_ids = list({bot.strategy_id for bot in bots})
    strategies_map = {}
    if strategy_ids:
        strategies = Strategy.query.filter(Strategy.id.in_(strategy_ids)).all()
        strategies_map = {s.id: s for s in strategies}

    result = []
    for bot in bots:
        strategy = strategies_map.get(bot.strategy_id)
        strategy_name = (strategy.title or strategy.name) if strategy else '(策略已删除)'
        result.append({
            'id': bot.id,
            'strategy_id': bot.strategy_id,
            'strategy_name': strategy_name,
            'initial_capital': f'{bot.initial_capital:.2f}',
            'status': bot.status,
            'created_at': format_beijing_iso(bot.created_at),
        })

    return ok(result)


@bp.get('/bots/<string:bot_id>/positions')
@jwt_required()
def get_bot_positions(bot_id: str):
    user_id = get_jwt_identity()
    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)

    positions = SimulationPosition.query.filter_by(bot_id=bot_id).all()
    return ok([_serialize_position(position) for position in positions])


@bp.get('/bots/<string:bot_id>/records')
@jwt_required()
def get_bot_records(bot_id: str):
    user_id = get_jwt_identity()
    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)

    records = (
        SimulationRecord.query
        .filter_by(bot_id=bot_id)
        .order_by(SimulationRecord.trade_date.asc())
        .all()
    )
    return ok([_serialize_record(record) for record in records])


@bp.get('/bots/<string:bot_id>/trades')
@jwt_required()
def get_bot_trades(bot_id: str):
    user_id = get_jwt_identity()
    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)

    trades = (
        SimulationTrade.query
        .filter_by(bot_id=bot_id)
        .order_by(SimulationTrade.trade_date.desc(), SimulationTrade.created_at.desc())
        .all()
    )
    return ok([_serialize_trade(trade) for trade in trades])


@bp.get('/bots/<string:bot_id>/stream')
def stream_bot(bot_id: str):
    # WARNING: 每个 SSE 连接会永久占用一个 WSGI worker 线程。
    # 生产环境必须使用 gevent/eventlet worker，否则并发 SSE 连接数受限于 worker 数量。
    user_id, error = _resolve_stream_user_id()
    if error:
        return error

    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)

    def generate():
        last_version = None
        last_heartbeat_at = time.monotonic()

        while True:
            current_version = _snapshot_version(bot_id)
            if current_version != last_version:
                payload = json.dumps(_build_bot_snapshot(bot_id))
                yield f'data: {payload}\n\n'
                last_version = current_version
                last_heartbeat_at = time.monotonic()
            elif time.monotonic() - last_heartbeat_at >= 30:
                yield f': heartbeat {datetime.now(timezone.utc).isoformat()}\n\n'
                last_heartbeat_at = time.monotonic()

            time.sleep(5)

    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


ALLOWED_PATCH_STATUSES = {'active', 'paused'}


@bp.patch('/bots/<string:bot_id>')
@jwt_required()
def update_bot_status(bot_id: str):
    user_id = get_jwt_identity()
    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', '机器人不存在或无权访问', 404)

    payload = request.get_json() or {}
    new_status = payload.get('status')
    if new_status not in ALLOWED_PATCH_STATUSES:
        return error_response(
            'VALIDATION_ERROR',
            f'status 必须为 active 或 paused，收到: {new_status}',
            422,
        )

    bot.status = new_status
    db.session.commit()

    return ok({
        'id': bot.id,
        'status': bot.status,
    })


@bp.delete('/bots/<string:bot_id>')
@jwt_required()
def delete_bot(bot_id: str):
    user_id = get_jwt_identity()
    bot = _get_bot_for_user(bot_id, user_id)
    if bot is None:
        return error_response('BOT_NOT_FOUND', '机器人不存在或无权访问', 404)

    bot.deleted_at = now_utc()
    db.session.commit()

    return ok({'deleted': True})
