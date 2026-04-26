import logging

from celery.utils.log import get_task_logger
from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import Post, PostComment, User, UserModerationRecord
from ..services.moderation import scan
from ..services.notifications import create_notification

logger = get_task_logger(__name__) if logging.getLogger().handlers else logging.getLogger(__name__)

MAX_WARNINGS = 3


def _moderate(user_id: str, target_type: str, target_id: str, content: str):
    matched = scan(content)
    if not matched:
        return {"status": "clean"}

    user = db.session.get(User, user_id)
    if user is None:
        return {"status": "user_not_found"}

    if target_type == "post":
        db.session.query(Post).filter_by(id=target_id).update({Post.is_hidden: True})
    elif target_type == "comment":
        db.session.query(PostComment).filter_by(id=target_id).update({PostComment.is_hidden: True})

    user.warning_count = (user.warning_count or 0) + 1
    action_taken = "warned"

    record = UserModerationRecord(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        matched_words=matched,
        action_taken=action_taken,
    )
    db.session.add(record)

    if user.warning_count >= MAX_WARNINGS:
        user.is_banned = True
        action_taken = "banned"
        record.action_taken = action_taken
        try:
            from ..utils.auth import blacklist_refresh_tokens, revoke_all_user_tokens
            active_tokens = revoke_all_user_tokens(user.id, reason="auto_ban_moderation")
            blacklist_refresh_tokens(active_tokens)
        except Exception:
            logger.exception("Failed to revoke tokens for user %s", user.id)

    if action_taken == "banned":
        title = "账号已被封禁"
        notification_content = (
            f"您发布的内容包含违规词汇（{', '.join(matched[:5])}），已被下架。"
            f"累计违规{user.warning_count}次，账号已被自动封禁。"
        )
    else:
        title = "内容违规警告"
        remaining = MAX_WARNINGS - user.warning_count
        notification_content = (
            f"您发布的内容包含违规词汇（{', '.join(matched[:5])}），已被下架。"
            f"这是第{user.warning_count}次警告，还剩{remaining}次将被封禁。"
        )

    create_notification(
        user_id=user_id,
        type="moderation_warning",
        title=title,
        content=notification_content,
    )

    db.session.commit()
    return {"status": "flagged", "matched": matched, "action": action_taken}


@celery_app.task(
    bind=True,
    name="app.tasks.moderation_tasks.moderate_content",
    soft_time_limit=30,
    time_limit=60,
)
def moderate_content(self, user_id: str, target_type: str, target_id: str, content: str):
    if has_app_context():
        return _moderate(user_id, target_type, target_id, content)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _moderate(user_id, target_type, target_id, content)
