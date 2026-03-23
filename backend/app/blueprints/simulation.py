from decimal import Decimal, InvalidOperation

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import SimulationBot, Strategy, User
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso

bp = Blueprint('simulation', __name__, url_prefix='/api/v1/simulation')

SLOT_LIMITS = {'free': 1, 'lite': 2, 'pro': 3, 'expert': 5}
ACTIVE_STATUSES = {'active'}


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response('USER_NOT_FOUND', 'user not found', 404)
    return user, None


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

    if capital <= 0:
        return error_response('VALIDATION_ERROR', 'initial_capital must be greater than zero', 422)

    slot_limit = SLOT_LIMITS.get(user.plan_level, SLOT_LIMITS['free'])
    active_count = (
        SimulationBot.query
        .filter(
            SimulationBot.user_id == user_id,
            SimulationBot.status.in_(ACTIVE_STATUSES),
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
