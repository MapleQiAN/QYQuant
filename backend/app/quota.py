import math

from .extensions import db
from .models import UserQuota


PLAN_LIMITS = {
    "free": 10,
    "go": 50,
    "plus": 200,
    "pro": 500,
    "ultra": math.inf,
}

PLAN_LEVEL_ALIASES = {
    # legacy renames – keep reading old DB values correctly
    "lite": "plus",
    "expert": "ultra",
    # older aliases
    "basic": "go",
    "enterprise": "ultra",
}


def normalize_plan_level(plan_level):
    return PLAN_LEVEL_ALIASES.get(plan_level or "free", plan_level or "free")


def get_plan_limit(plan_level):
    normalized_plan_level = normalize_plan_level(plan_level)
    return PLAN_LIMITS.get(normalized_plan_level, PLAN_LIMITS["free"])


def serialize_plan_limit(plan_level):
    limit = get_plan_limit(plan_level)
    if math.isinf(limit):
        return "unlimited"
    return int(limit)


def ensure_user_quota(user_id, plan_level="free"):
    normalized_plan_level = normalize_plan_level(plan_level)
    quota = db.session.get(UserQuota, user_id)
    if quota is None:
        quota = UserQuota(user_id=user_id, plan_level=normalized_plan_level, used_count=0)
        db.session.add(quota)
        db.session.flush()
        return quota

    current_plan_level = normalize_plan_level(quota.plan_level)
    if quota.plan_level != current_plan_level:
        quota.plan_level = current_plan_level

    if plan_level and quota.plan_level != normalized_plan_level:
        quota.plan_level = normalized_plan_level
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
