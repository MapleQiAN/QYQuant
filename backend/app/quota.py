import math

from .extensions import db
from .models import BacktestQuotaLedger, UserQuota
from .utils.time import now_utc


PLAN_LIMITS = {
    "free": 30,
    "basic": 100,
    "go": 100,
    "plus": 300,
    "pro": 800,
    "ultra": math.inf,
}

PLAN_LEVEL_ALIASES = {
    # legacy renames – keep reading old DB values correctly
    "lite": "plus",
    "expert": "ultra",
    # older aliases
    "enterprise": "ultra",
}

BOT_SLOT_LIMITS = {
    "free": 1,
    "go": 2,
    "plus": 3,
    "pro": 5,
    "ultra": 10,
}


def normalize_plan_level(plan_level):
    return PLAN_LEVEL_ALIASES.get(plan_level or "free", plan_level or "free")


def get_plan_limit(plan_level):
    normalized_plan_level = normalize_plan_level(plan_level)
    return PLAN_LIMITS.get(normalized_plan_level, PLAN_LIMITS["free"])


def get_bot_slot_limit(plan_level):
    normalized_plan_level = normalize_plan_level(plan_level)
    return BOT_SLOT_LIMITS.get(normalized_plan_level, BOT_SLOT_LIMITS["free"])


def serialize_plan_limit(plan_level):
    limit = get_plan_limit(plan_level)
    if math.isinf(limit):
        return "unlimited"
    return int(limit)


def ensure_user_quota(user_id, plan_level=None):
    normalized_plan_level = normalize_plan_level(plan_level or "free")
    quota = db.session.get(UserQuota, user_id)
    if quota is None:
        quota = UserQuota(user_id=user_id, plan_level=normalized_plan_level, used_count=0)
        db.session.add(quota)
        db.session.flush()
        return quota

    current_plan_level = normalize_plan_level(quota.plan_level)
    if quota.plan_level != current_plan_level:
        quota.plan_level = current_plan_level

    if plan_level is not None and quota.plan_level != normalized_plan_level:
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


def reserve_backtest_quota(user_id, job_id):
    quota = ensure_user_quota(user_id)
    ledger = db.session.get(BacktestQuotaLedger, job_id)
    if ledger is not None:
        return ledger.status in {'reserved', 'consumed'}

    limit = get_plan_limit(quota.plan_level)
    if math.isinf(limit):
        UserQuota.query.filter_by(user_id=user_id).update(
            {UserQuota.used_count: UserQuota.used_count + 1},
            synchronize_session=False,
        )
        db.session.add(BacktestQuotaLedger(job_id=job_id, user_id=user_id, status='reserved'))
        db.session.flush()
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
    if updated != 1:
        return False

    db.session.add(BacktestQuotaLedger(job_id=job_id, user_id=user_id, status='reserved'))
    db.session.flush()
    return True


def consume_backtest_quota(job_id):
    ledger = db.session.get(BacktestQuotaLedger, job_id)
    if ledger is None:
        return False
    if ledger.status == 'consumed':
        return True
    if ledger.status != 'reserved':
        return False
    ledger.status = 'consumed'
    ledger.finalized_at = now_utc()
    db.session.flush()
    return True


def release_backtest_quota(job_id):
    ledger = db.session.get(BacktestQuotaLedger, job_id)
    if ledger is None:
        return False
    if ledger.status == 'released':
        return True
    if ledger.status != 'reserved':
        return False

    quota = db.session.get(UserQuota, ledger.user_id)
    if quota is not None and quota.used_count > 0:
        quota.used_count -= 1

    ledger.status = 'released'
    ledger.finalized_at = now_utc()
    db.session.flush()
    return True
