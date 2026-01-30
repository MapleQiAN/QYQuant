from flask import request
from flask_jwt_extended import create_access_token
from flask_smorest import Blueprint
from werkzeug.security import check_password_hash

from ..models import User
from ..utils.response import ok

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.post('/login')
def login():
    payload = request.get_json() or {}
    user = User.query.filter_by(email=payload.get('email')).first()
    if not user or not check_password_hash(user.password_hash, payload.get('password', '')):
        return {"code": 40100, "message": "unauthorized", "details": None}, 401
    token = create_access_token(identity=user.id)
    return ok({"access_token": token})
