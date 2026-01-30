from flask import Blueprint

from ..utils.response import ok

bp = Blueprint('health', __name__)


@bp.get('/api/health')
def health():
    return ok({"status": "ok"})
