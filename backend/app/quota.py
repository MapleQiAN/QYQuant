import math

from .extensions import db
from .models import UserQuota


PLAN_LIMITS = {
    "free": 10,
    "basic": 100,
    "pro": 500,
    "enterprise": math.inf,
}


def get_plan_limit(plan_level):
    return PLAN_LIMITS.get(plan_level or "free", PLAN_LIMITS["free"])


def serialize_plan_limit(plan_level):
    limit = get_plan_limit(plan_level)
    if math.isinf(limit):
        return "unlimited"
    return int(limit)


def ensure_user_quota(user_id, plan_level="free"):
    quota = db.session.get(UserQuota, user_id)
    if quota is None:
        quota = UserQuota(user_id=user_id, plan_level=plan_level, used_count=0)
        db.session.add(quota)
        db.session.flush()
    elif not quota.plan_level:
        quota.plan_level = plan_level
    elif plan_level and quota.plan_level != plan_level:
        quota.plan_level = plan_level
    return quota


def has_remaining_quota(quota):
    limit = get_plan_limit(quota.plan_level)
    if math.isinf(limit):
        return True
    return quota.used_count < limit


def consume_quota(user_id):
    quota = ensure_user_quota(user_id)
    limit = get_plan_limit(quota.plan_level)

    if math.isinf(limit):
        UserQuota.query.filter_by(user_id=user_id).update(
            {UserQuota.used_count: UserQuota.used_count + 1},
            synchronize_session=False,
        )
        return True

    updated = (
        UserQuota.query.filter(
            UserQuota.user_id == user_id,
            UserQuota.used_count < int(limit),
        ).update(
            {UserQuota.used_count: UserQuota.used_count + 1},
            synchronize_session=False,
        )
    )
    return updated == 1
