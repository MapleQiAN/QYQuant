from functools import wraps

from flask_jwt_extended import current_user, jwt_required

from .response import error_response


def require_admin(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if current_user is None or getattr(current_user, "role", None) != "admin":
            return error_response("FORBIDDEN", "管理员权限不足", 403)
        return fn(*args, **kwargs)

    return wrapper
