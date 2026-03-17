from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import RefreshToken, User


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
