from flask_smorest import Blueprint

from ..models import Strategy
from ..schemas import StrategySchema
from ..utils.response import ok

bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')


@bp.get('/recent')
def recent():
    items = Strategy.query.order_by(Strategy.last_update.desc()).limit(10).all()
    return ok(StrategySchema(many=True).dump(items))
