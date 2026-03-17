from app.schemas import UserSchema


def test_user_schema_shape():
    data = UserSchema().dump(
        {
            "id": "u1",
            "phone": "13800138000",
            "nickname": "量化小白",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "hello",
            "role": "user",
            "plan_level": "free",
            "is_banned": False,
        }
    )
    assert data["phone"] == "13800138000"
    assert data["nickname"] == "量化小白"
    assert data["plan_level"] == "free"
