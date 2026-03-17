from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from ..extensions import db
from ..models import User
from ..schemas import UserPrivateSchema, UserPublicSchema, UserUpdateSchema
from ..utils.response import error_response, ok

bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

_private_schema = UserPrivateSchema()
_public_schema = UserPublicSchema()
_update_schema = UserUpdateSchema()


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response("USER_NOT_FOUND", "user not found", 404)
    return user, None


def _validation_error(exc):
    messages = []
    for field, errors in exc.messages.items():
        if errors:
            messages.append(f"{field}: {errors[0]}")
    message = "; ".join(messages) if messages else "invalid payload"
    return error_response("VALIDATION_ERROR", message, 422, details=exc.messages)


@bp.get('/me')
@jwt_required()
def me():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error
    return ok(_private_schema.dump(user))


@bp.patch('/me')
@jwt_required()
def update_me():
    user, error = _get_user_or_404(get_jwt_identity())
    if error:
        return error

    payload = request.get_json() or {}
    try:
        updates = _update_schema.load(payload, partial=True)
    except ValidationError as exc:
        return _validation_error(exc)

    for field, value in updates.items():
        setattr(user, field, value)

    db.session.commit()
    return ok(_private_schema.dump(user))


@bp.get('/<user_id>')
def get_user_profile(user_id):
    user, error = _get_user_or_404(user_id)
    if error:
        return error
    return ok(_public_schema.dump(user))
