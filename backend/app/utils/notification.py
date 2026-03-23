from ..models import Notification


def create_notification(session, user_id, type, title, content=None):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        is_read=False,
    )
    session.add(notification)
    return notification
