from ..extensions import db
from ..utils.notification import create_notification as _create_notification


def create_notification(user_id, type, title, content=None):
    return _create_notification(
        db.session,
        user_id=user_id,
        type=type,
        title=title,
        content=content,
    )
