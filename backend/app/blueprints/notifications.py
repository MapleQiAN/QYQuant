from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import Notification
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso

bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


@bp.get('/unread-count')
@jwt_required()
def unread_count():
    user_id = get_jwt_identity()
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return ok({'count': count})


@bp.get('')
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 20, type=int), 1), 100)

    pagination = (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = [
        {
            'id': item.id,
            'type': item.type,
            'title': item.title,
            'content': item.content,
            'is_read': bool(item.is_read),
            'created_at': format_beijing_iso(item.created_at),
        }
        for item in pagination.items
    ]
    return ok(items, meta={'total': pagination.total, 'page': pagination.page, 'per_page': pagination.per_page})


@bp.patch('/<notification_id>/read')
@jwt_required()
def mark_notification_read(notification_id):
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification is None:
        return error_response('NOTIFICATION_NOT_FOUND', 'Notification not found', 404)

    notification.is_read = True
    db.session.commit()
    return ok({'ok': True})
