from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import BacktestJob, RefreshToken, Strategy, User, UserQuota


def test_user_model_fields(app):
    with app.app_context():
        db.create_all()
        user = User(phone="13800138000", nickname="量化小白")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.phone == "13800138000"
        assert user.nickname == "量化小白"
        assert user.role == "user"
        assert user.plan_level == "free"
        assert user.is_banned is False
        assert user.deleted_at is None


def test_refresh_token_model_persists_hash_and_jti(app):
    with app.app_context():
        db.create_all()
        user = User(phone="13800138000", nickname="量化小白")
        db.session.add(user)
        db.session.flush()

        token = RefreshToken(
            user_id=user.id,
            token_hash="abc123",
            jti="token-jti",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(token)
        db.session.commit()

        saved = RefreshToken.query.filter_by(user_id=user.id).one()
        assert saved.token_hash == "abc123"
        assert saved.jti == "token-jti"
        assert saved.revoked_at is None


def test_backtest_job_model_persists_status_and_payload(app):
    with app.app_context():
        user = User(phone="13800138000", nickname="量化小白")
        strategy = Strategy(name="Demo", symbol="BTCUSDT", status="draft")
        db.session.add_all([user, strategy])
        db.session.flush()

        job = BacktestJob(
            user_id=user.id,
            strategy_id=strategy.id,
            params={"symbol": "BTCUSDT", "limit": 60},
        )
        db.session.add(job)
        db.session.commit()

        saved = db.session.get(BacktestJob, job.id)
        assert saved is not None
        assert saved.status == "pending"
        assert saved.params == {"symbol": "BTCUSDT", "limit": 60}
        assert saved.result_summary is None
        assert saved.created_at is not None


def test_user_quota_requires_unique_user_id(app):
    with app.app_context():
        user = User(phone="13800138001", nickname="额度用户")
        db.session.add(user)
        db.session.flush()

        quota = UserQuota(user_id=user.id, plan_level="basic")
        db.session.add(quota)
        db.session.commit()

        duplicate = UserQuota(user_id=user.id, plan_level="pro")
        db.session.expunge(quota)
        db.session.add(duplicate)

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
