from datetime import datetime, timezone

import pytest
from marshmallow import ValidationError

from app.schemas import UserPrivateSchema, UserPublicSchema, UserUpdateSchema


def test_user_private_schema_masks_phone_and_formats_times():
    data = UserPrivateSchema().dump(
        {
            "id": "u1",
            "phone": "13800138000",
            "nickname": "Trader",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "hello",
            "role": "user",
            "plan_level": "free",
            "is_banned": False,
            "onboarding_completed": False,
            "created_at": datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 3, 14, 11, 30, 0, tzinfo=timezone.utc),
        }
    )

    assert data["phone"] == "138****8000"
    assert data["nickname"] == "Trader"
    assert data["plan_level"] == "free"
    assert data["created_at"] == "2026-03-14T18:00:00+08:00"
    assert data["updated_at"] == "2026-03-14T19:30:00+08:00"


def test_user_public_schema_excludes_sensitive_fields():
    data = UserPublicSchema().dump(
        {
            "id": "u1",
            "phone": "13800138000",
            "nickname": "Trader",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "hello",
            "is_banned": True,
            "created_at": datetime(2026, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
        }
    )

    assert data["id"] == "u1"
    assert data["nickname"] == "Trader"
    assert data["is_banned"] is True
    assert data["created_at"] == "2026-03-14T18:00:00+08:00"
    assert "phone" not in data


def test_user_update_schema_validates_lengths():
    schema = UserUpdateSchema()

    assert schema.load({"nickname": "Valid", "bio": "x" * 200})["nickname"] == "Valid"

    with pytest.raises(ValidationError):
        schema.load({"nickname": "A"})

    with pytest.raises(ValidationError):
        schema.load({"bio": "x" * 201})
