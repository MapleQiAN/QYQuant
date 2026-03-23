from flask_smorest import Blueprint

from ..utils.auth_helpers import require_admin
from ..utils.response import ok

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@bp.get("/health")
@require_admin
def admin_health():
    return ok({"status": "ok", "scope": "admin"})
