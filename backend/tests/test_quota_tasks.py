from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import AuditLog, Notification, Subscription, User, UserQuota


BEIJING_TZ = timezone(timedelta(hours=8))


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        current = cls(2026, 3, 1, 8, 30, tzinfo=BEIJING_TZ)
        if tz is None:
            return current.replace(tzinfo=None)
        return current.astimezone(tz)


def _seed_user_quota(user_id, *, plan_level="free", used_count=0, reset_at=None):
    quota = UserQuota(
        user_id=user_id,
        plan_level=plan_level,
        used_count=used_count,
        reset_at=reset_at,
    )
    db.session.add(quota)
    return quota


def _assert_beijing_month_start(value, *, year, month):
    if value.tzinfo is None:
        assert value == datetime(year, month, 1, 0, 0)
        return

    localized = value.astimezone(BEIJING_TZ)
    assert localized == datetime(year, month, 1, 0, 0, tzinfo=BEIJING_TZ)


def test_reset_monthly_quotas_resets_all_used_counts(monkeypatch, app):
    from app.tasks.quota_tasks import _reset_monthly_quotas

    monkeypatch.setattr("app.tasks.quota_tasks.datetime", _FixedDatetime)

    with app.app_context():
        user_one = User(phone="13800138300", nickname="QuotaResetOne")
        user_two = User(phone="13800138301", nickname="QuotaResetTwo")
        db.session.add_all([user_one, user_two])
        db.session.flush()
        _seed_user_quota(user_one.id, plan_level="lite", used_count=12)
        _seed_user_quota(user_two.id, plan_level="pro", used_count=48)
        db.session.commit()

        result = _reset_monthly_quotas()

        assert result == {"reset_count": 2, "downgraded_count": 0}

        quotas = UserQuota.query.order_by(UserQuota.user_id.asc()).all()
        assert [quota.used_count for quota in quotas] == [0, 0]
        for quota in quotas:
            _assert_beijing_month_start(quota.reset_at, year=2026, month=4)


def test_reset_monthly_quotas_downgrades_expired_subscriptions(monkeypatch, app):
    from app.tasks.quota_tasks import _reset_monthly_quotas

    monkeypatch.setattr("app.tasks.quota_tasks.datetime", _FixedDatetime)

    with app.app_context():
        user = User(phone="13800138302", nickname="ExpiredSubscriber", plan_level="pro")
        db.session.add(user)
        db.session.flush()
        _seed_user_quota(user.id, plan_level="pro", used_count=9)
        db.session.add(
            Subscription(
                user_id=user.id,
                plan_level="pro",
                starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ends_at=datetime(2026, 2, 28, 15, 59, tzinfo=timezone.utc),
                status="active",
                payment_provider="wechat",
            )
        )
        db.session.commit()

        result = _reset_monthly_quotas()

        assert result == {"reset_count": 1, "downgraded_count": 1}

        subscription = Subscription.query.filter_by(user_id=user.id).one()
        assert subscription.status == "expired"

        refreshed_user = db.session.get(User, user.id)
        assert refreshed_user.plan_level == "free"

        quota = db.session.get(UserQuota, user.id)
        assert quota.plan_level == "free"
        assert quota.used_count == 0
        _assert_beijing_month_start(quota.reset_at, year=2026, month=4)

        audit_log = AuditLog.query.filter_by(action="subscription_expired", target_id=user.id).one()
        assert audit_log.details["old_plan_level"] == "pro"
        assert audit_log.details["new_plan_level"] == "free"

        notification = Notification.query.filter_by(
            user_id=user.id,
            type="subscription_expired",
        ).one()
        assert "pro" in notification.content.lower()


def test_reset_monthly_quotas_is_idempotent(monkeypatch, app):
    from app.tasks.quota_tasks import _reset_monthly_quotas

    monkeypatch.setattr("app.tasks.quota_tasks.datetime", _FixedDatetime)

    with app.app_context():
        user = User(phone="13800138303", nickname="IdempotentQuotaUser", plan_level="lite")
        db.session.add(user)
        db.session.flush()
        _seed_user_quota(user.id, plan_level="lite", used_count=5)
        db.session.add(
            Subscription(
                user_id=user.id,
                plan_level="lite",
                starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ends_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
                status="active",
                payment_provider="wechat",
            )
        )
        db.session.commit()

        first = _reset_monthly_quotas()
        second = _reset_monthly_quotas()

        assert first == {"reset_count": 1, "downgraded_count": 1}
        assert second == {"reset_count": 1, "downgraded_count": 0}

        quota = db.session.get(UserQuota, user.id)
        assert quota.used_count == 0
        assert AuditLog.query.filter_by(action="subscription_expired", target_id=user.id).count() == 1
        assert Notification.query.filter_by(user_id=user.id, type="subscription_expired").count() == 1


def test_reset_skips_users_with_other_active_subscription(monkeypatch, app):
    from app.tasks.quota_tasks import _reset_monthly_quotas

    monkeypatch.setattr("app.tasks.quota_tasks.datetime", _FixedDatetime)

    with app.app_context():
        user = User(phone="13800138304", nickname="MixedSubscriptionUser", plan_level="expert")
        db.session.add(user)
        db.session.flush()
        _seed_user_quota(user.id, plan_level="expert", used_count=17)
        db.session.add_all(
            [
                Subscription(
                    user_id=user.id,
                    plan_level="lite",
                    starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    ends_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
                    status="active",
                    payment_provider="wechat",
                ),
                Subscription(
                    user_id=user.id,
                    plan_level="expert",
                    starts_at=datetime(2026, 2, 16, tzinfo=timezone.utc),
                    ends_at=datetime(2026, 3, 31, tzinfo=timezone.utc),
                    status="active",
                    payment_provider="wechat",
                ),
            ]
        )
        db.session.commit()

        result = _reset_monthly_quotas()

        assert result == {"reset_count": 1, "downgraded_count": 0}

        expired_subscription = Subscription.query.filter_by(plan_level="lite").one()
        assert expired_subscription.status == "expired"

        refreshed_user = db.session.get(User, user.id)
        assert refreshed_user.plan_level == "expert"

        quota = db.session.get(UserQuota, user.id)
        assert quota.plan_level == "expert"
        assert AuditLog.query.filter_by(action="subscription_expired", target_id=user.id).count() == 0
        assert Notification.query.filter_by(user_id=user.id, type="subscription_expired").count() == 0


def test_celery_app_registers_monthly_quota_reset_schedule():
    from app.celery_app import celery_app

    assert "app.tasks.quota_tasks" in celery_app.conf.imports

    schedule = celery_app.conf.beat_schedule["reset-monthly-quotas"]
    assert schedule["task"] == "app.tasks.quota_tasks.reset_monthly_quotas"
    assert schedule["options"] == {"queue": "default"}
