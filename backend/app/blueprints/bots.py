from flask import request
from flask_smorest import Blueprint

from ..extensions import db
from ..models import BotInstance, Order
from ..schemas import BotSchema
from ..utils.response import ok

bp = Blueprint('bots', __name__, url_prefix='/api/bots')


@bp.post('')
def create_bot():
    payload = request.get_json() or {}
    bot = BotInstance(
        name=payload.get('name', 'Bot'),
        strategy=payload.get('strategy_id', ''),
        status='active',
        profit=0,
        runtime='0d',
        capital=payload.get('capital', 0),
        tags=payload.get('tags', []),
        paper=True,
    )
    db.session.add(bot)
    db.session.commit()
    return ok(BotSchema().dump(bot))


@bp.get('/recent')
def recent():
    items = BotInstance.query.order_by(BotInstance.created_at.desc()).limit(10).all()
    return ok(BotSchema(many=True).dump(items))


@bp.patch('/<bot_id>/status')
def update_status(bot_id):
    payload = request.get_json() or {}
    status = payload.get('status')
    if status == 'running':
        status = 'active'
    bot = BotInstance.query.get(bot_id)
    bot.status = status
    db.session.commit()
    return ok(BotSchema().dump(bot))


@bp.get('/<bot_id>/performance')
def performance(bot_id):
    orders = Order.query.filter_by(bot_id=bot_id).all()
    return ok({"equity": [], "orders": []})
