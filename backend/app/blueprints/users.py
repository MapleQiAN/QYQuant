from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..models import User
from ..schemas import UserSchema
from ..utils.response import ok

bp = Blueprint('users', __name__, url_prefix='/api/users')


@bp.get('/me')
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    return ok(UserSchema().dump(user))
