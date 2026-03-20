from ..extensions import db
from ..models import Notification


def create_notification(user_id, type, title, content=None):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
    )
    db.session.add(notification)
    return notification
