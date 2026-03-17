from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..models import User
from ..schemas import UserSchema
from ..utils.response import ok

bp = Blueprint('users', __name__, url_prefix='/api/users')


@bp.get('/me')
@jwt_required()
def me():
    user = db.session.get(User, get_jwt_identity())
    if user is None:
        return {"error": {"code": "USER_NOT_FOUND", "message": "用户不存在"}}, 404
    return ok(UserSchema().dump(user))
