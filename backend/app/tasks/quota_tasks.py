import logging
from datetime import datetime

from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import AuditLog, Subscription, User, UserQuota
from ..quota import normalize_plan_level
from ..services.notifications import create_notification
from ..utils.time import BEIJING_TZ, next_month_start_beijing, now_utc


logger = logging.getLogger(__name__)

PLAN_DISPLAY_NAMES = {
    "lite": "lite",
    "pro": "pro",
    "expert": "expert",
}


def _reset_monthly_quotas():
    next_reset = next_month_start_beijing(datetime.now(BEIJING_TZ))
    expired_subscriptions = Subscription.query.filter(
        Subscription.status == "active",
        Subscription.ends_at < now_utc(),
    ).all()

    downgraded_count = 0
    processed_users = set()

    for subscription in expired_subscriptions:
        subscription.status = "expired"
        if subscription.user_id in processed_users:
            continue
        processed_users.add(subscription.user_id)

        has_active_subscription = (
            Subscription.query.filter(
                Subscription.user_id == subscription.user_id,
                Subscription.status == "active",
                Subscription.ends_at >= now_utc(),
            ).count() > 0
        )
        if has_active_subscription:
            continue

        user = db.session.get(User, subscription.user_id)
        quota = db.session.get(UserQuota, subscription.user_id)
        if user is None:
            continue

        old_plan = normalize_plan_level(user.plan_level)
        if old_plan == "free":
            if quota is not None:
                quota.plan_level = "free"
            continue

        user.plan_level = "free"
        if quota is not None:
            quota.plan_level = "free"

        db.session.add(
            AuditLog(
                operator_id=None,
                action="subscription_expired",
                target_type="user",
                target_id=subscription.user_id,
                details={
                    "old_plan_level": old_plan,
                    "new_plan_level": "free",
                    "subscription_id": subscription.id,
                },
            )
        )
        create_notification(
            user_id=subscription.user_id,
            type="subscription_expired",
            title="套餐已过期",
            content=(
                f"您的 {PLAN_DISPLAY_NAMES.get(old_plan, old_plan)} 套餐已过期，"
                "已恢复为免费套餐。"
            ),
        )
        downgraded_count += 1

    quotas = UserQuota.query.all()
    for quota in quotas:
        quota.used_count = 0
        quota.reset_at = next_reset
    reset_count = len(quotas)

    db.session.commit()
    logger.info(
        "Monthly quota reset completed: %d quotas reset, %d subscriptions downgraded",
        reset_count,
        downgraded_count,
    )
    return {"reset_count": reset_count, "downgraded_count": downgraded_count}


@celery_app.task(bind=True, name="app.tasks.quota_tasks.reset_monthly_quotas")
def reset_monthly_quotas(self):
    if has_app_context():
        return _reset_monthly_quotas()

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _reset_monthly_quotas()
