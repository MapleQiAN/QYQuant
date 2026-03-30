from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    BacktestJob,
    IntegrationProvider,
    RefreshToken,
    Strategy,
    StrategyParameterPreset,
    User,
    UserIntegration,
    UserIntegrationSecret,
    UserQuota,
)


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


def test_integration_models_separate_metadata_from_secret_payload(app):
    with app.app_context():
        user = User(phone="13800138003", nickname="Integration User")
        provider = IntegrationProvider(
            key="longport",
            name="LongPort",
            type="broker_account",
            mode="hosted",
            capabilities={"account_summary": True, "positions": True},
            config_schema={"fields": ["app_key", "app_secret", "access_token"]},
        )
        db.session.add_all([user, provider])
        db.session.flush()

        integration = UserIntegration(
            user_id=user.id,
            provider_key=provider.key,
            display_name="Primary LongPort",
            status="active",
            config_public={"region": "hk"},
        )
        db.session.add(integration)
        db.session.flush()

        secret = UserIntegrationSecret(
            integration_id=integration.id,
            encrypted_payload="ciphertext",
            schema_version=1,
        )
        db.session.add(secret)
        db.session.commit()

        saved_integration = db.session.get(UserIntegration, integration.id)
        saved_secret = db.session.get(UserIntegrationSecret, integration.id)

        assert saved_integration is not None
        assert saved_integration.provider_key == "longport"
        assert saved_integration.config_public == {"region": "hk"}
        assert saved_secret is not None
        assert saved_secret.encrypted_payload == "ciphertext"
        assert saved_secret.schema_version == 1


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


def test_strategy_parameter_preset_persists_json_payload(app):
    with app.app_context():
        user = User(phone="13800138002", nickname="预设用户")
        strategy = Strategy(name="Preset Strategy", symbol="BTCUSDT", status="draft")
        db.session.add_all([user, strategy])
        db.session.flush()

        preset = StrategyParameterPreset(
            strategy_id=strategy.id,
            user_id=user.id,
            name="稳健版",
            parameters={"window": 20, "direction": "long"},
        )
        db.session.add(preset)
        db.session.commit()

        saved = db.session.get(StrategyParameterPreset, preset.id)
        assert saved is not None
        assert saved.name == "稳健版"
        assert saved.parameters == {"window": 20, "direction": "long"}
        assert saved.created_at is not None
