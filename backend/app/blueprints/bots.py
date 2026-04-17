from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..services import bots as bots_service
from ..utils.response import error_response, ok

bp = Blueprint('bots', __name__, url_prefix='/api/bots')


@bp.post('')
@jwt_required()
def create_bot():
    payload = request.get_json() or {}
    try:
        data = bots_service.create_bot(user_id=get_jwt_identity(), payload=payload)
    except bots_service.BotServiceError as exc:
        return error_response(exc.code, exc.message, exc.status)
    return ok(data), 201


@bp.get('')
@jwt_required()
def list_bots():
    return ok(bots_service.list_bots(get_jwt_identity()))


@bp.get('/recent')
@jwt_required()
def recent():
    return ok(bots_service.list_recent_bots(get_jwt_identity()))


@bp.patch('/<bot_id>/status')
@jwt_required()
def update_status(bot_id):
    bot = bots_service.get_bot_for_user(bot_id, get_jwt_identity())
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)

    payload = request.get_json() or {}
    status = payload.get('status')
    if status == 'running':
        status = 'active'
    try:
        data = bots_service.update_bot_status(bot=bot, status=status)
    except bots_service.BotServiceError as exc:
        return error_response(exc.code, exc.message, exc.status)
    return ok(data)


@bp.get('/<bot_id>/positions')
@jwt_required()
def positions(bot_id):
    bot = bots_service.get_bot_for_user(bot_id, get_jwt_identity())
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)
    return ok(bots_service.get_bot_positions(bot=bot))


@bp.get('/<bot_id>/performance')
@jwt_required()
def performance(bot_id):
    bot = bots_service.get_bot_for_user(bot_id, get_jwt_identity())
    if bot is None:
        return error_response('BOT_NOT_FOUND', 'Bot not found', 404)
    return ok(bots_service.get_bot_performance(bot=bot))
