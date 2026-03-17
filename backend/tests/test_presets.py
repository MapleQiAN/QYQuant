from app.extensions import db
from app.models import Strategy, StrategyParameterPreset


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone, nickname):
    _seed_code(client.application, phone)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_strategy_presets_crud_for_current_user(client, app):
    token, user_id = _login_user(client, phone="13800138031", nickname="PresetOwner")

    with app.app_context():
        db.session.add(
            Strategy(
                id="shared-strategy",
                name="Shared Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=None,
            )
        )
        db.session.commit()

    create_response = client.post(
        "/api/v1/strategies/shared-strategy/presets",
        headers=_auth_headers(token),
        json={
            "name": "稳健版",
            "parameters": {"window": 20, "direction": "long"},
        },
    )

    assert create_response.status_code == 200
    created = create_response.json["data"]
    assert created["name"] == "稳健版"
    assert created["strategyId"] == "shared-strategy"
    assert created["parameters"] == {"window": 20, "direction": "long"}

    list_response = client.get(
        "/api/v1/strategies/shared-strategy/presets",
        headers=_auth_headers(token),
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json["data"]] == [created["id"]]

    update_response = client.put(
        f"/api/v1/strategies/shared-strategy/presets/{created['id']}",
        headers=_auth_headers(token),
        json={
            "name": "激进版",
            "parameters": {"window": 10, "direction": "both"},
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json["data"]
    assert updated["name"] == "激进版"
    assert updated["parameters"] == {"window": 10, "direction": "both"}

    delete_response = client.delete(
        f"/api/v1/strategies/shared-strategy/presets/{created['id']}",
        headers=_auth_headers(token),
    )

    assert delete_response.status_code == 200
    assert delete_response.json["data"]["deletedId"] == created["id"]

    with app.app_context():
        assert StrategyParameterPreset.query.filter_by(user_id=user_id).count() == 0


def test_strategy_presets_are_scoped_to_current_user(client, app):
    owner_token, owner_id = _login_user(client, phone="13800138032", nickname="PresetOwner")
    viewer_token, viewer_id = _login_user(client, phone="13800138033", nickname="PresetViewer")

    with app.app_context():
        db.session.add(
            Strategy(
                id="shared-strategy",
                name="Shared Strategy",
                symbol="BTCUSDT",
                status="draft",
                owner_id=None,
            )
        )
        db.session.flush()
        preset = StrategyParameterPreset(
            strategy_id="shared-strategy",
            user_id=owner_id,
            name="Owner Preset",
            parameters={"window": 30},
        )
        db.session.add(preset)
        db.session.commit()
        preset_id = preset.id

    list_response = client.get(
        "/api/v1/strategies/shared-strategy/presets",
        headers=_auth_headers(viewer_token),
    )

    assert list_response.status_code == 200
    assert list_response.json["data"] == []

    update_response = client.put(
        f"/api/v1/strategies/shared-strategy/presets/{preset_id}",
        headers=_auth_headers(viewer_token),
        json={"name": "Hijacked", "parameters": {"window": 5}},
    )
    assert update_response.status_code == 404
    assert update_response.json["error"]["code"] == "PRESET_NOT_FOUND"

    delete_response = client.delete(
        f"/api/v1/strategies/shared-strategy/presets/{preset_id}",
        headers=_auth_headers(viewer_token),
    )
    assert delete_response.status_code == 404
    assert delete_response.json["error"]["code"] == "PRESET_NOT_FOUND"

    with app.app_context():
        saved = db.session.get(StrategyParameterPreset, preset_id)
        assert saved is not None
        assert saved.user_id == owner_id
        assert saved.parameters == {"window": 30}
