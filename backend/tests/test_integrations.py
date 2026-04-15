from app.extensions import db
from app.models import IntegrationProvider, User, UserIntegration, UserIntegrationSecret


def _login_user(client, email="integration@example.com", nickname="Trader"):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secret123!", "nickname": nickname},
    )
    assert register.status_code == 200
    return register.json["access_token"], register.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_provider(app, *, key, name, provider_type, mode, capabilities, config_schema):
    with app.app_context():
        provider = IntegrationProvider(
            key=key,
            name=name,
            type=provider_type,
            mode=mode,
            capabilities=capabilities,
            config_schema=config_schema,
        )
        db.session.add(provider)
        db.session.commit()


def test_list_integration_providers_requires_auth(client):
    response = client.get("/api/v1/integrations/providers")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_list_integration_providers_returns_enabled_provider_catalog(client):
    token, _ = _login_user(client)

    response = client.get("/api/v1/integrations/providers", headers=_auth_headers(token))

    assert response.status_code == 200
    assert any(item["key"] == "openai_compatible" for item in response.json["data"])
    assert any(item["key"] == "joinquant" for item in response.json["data"])
    assert any(item["key"] == "longport" for item in response.json["data"])


def test_create_integration_persists_metadata_and_encrypted_secret(client, app):
    token, user_id = _login_user(client, email="create@example.com", nickname="Creator")
    _seed_provider(
        app,
        key="longport",
        name="LongPort",
        provider_type="broker_account",
        mode="hosted",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"fields": ["app_key", "app_secret", "access_token"]},
    )

    response = client.post(
        "/api/v1/integrations",
        headers=_auth_headers(token),
        json={
            "provider_key": "longport",
            "display_name": "Main Account",
            "config_public": {"region": "hk"},
            "secret_payload": {
                "app_key": "key-1",
                "app_secret": "secret-1",
                "access_token": "token-1",
            },
        },
    )

    assert response.status_code == 201
    data = response.json["data"]
    assert data["provider_key"] == "longport"
    assert data["display_name"] == "Main Account"
    assert data["config_public"] == {"region": "hk"}
    assert "secret_payload" not in data

    with app.app_context():
        saved = UserIntegration.query.filter_by(user_id=user_id, provider_key="longport").one()
        secret = db.session.get(UserIntegrationSecret, saved.id)
        assert secret is not None
        assert secret.encrypted_payload != '{"access_token": "token-1", "app_key": "key-1", "app_secret": "secret-1"}'


def test_create_integration_validates_public_fields_separately_from_secrets(client, app):
    token, _ = _login_user(client, email="gmtrade@example.com", nickname="GMTradeUser")
    _seed_provider(
        app,
        key="gmtrade",
        name="GMTrade",
        provider_type="broker_account",
        mode="hosted",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"public_fields": ["account_id", "endpoint"], "secret_fields": ["token"]},
    )

    response = client.post(
        "/api/v1/integrations",
        headers=_auth_headers(token),
        json={
            "provider_key": "gmtrade",
            "display_name": "Missing Account Id",
            "config_public": {"endpoint": "api.myquant.cn:9000"},
            "secret_payload": {"token": "token-1"},
        },
    )

    assert response.status_code == 422
    assert "account_id" in response.json["error"]["message"]


def test_validate_and_read_broker_integration_uses_adapter_contract(client, app, monkeypatch):
    token, user_id = _login_user(client, email="broker@example.com", nickname="BrokerUser")
    _seed_provider(
        app,
        key="longport",
        name="LongPort",
        provider_type="broker_account",
        mode="hosted",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"fields": ["app_key", "app_secret", "access_token"]},
    )

    with app.app_context():
        integration = UserIntegration(
            user_id=user_id,
            provider_key="longport",
            display_name="Broker Account",
            status="active",
            config_public={"region": "hk"},
        )
        db.session.add(integration)
        db.session.flush()
        db.session.add(
            UserIntegrationSecret(
                integration_id=integration.id,
                encrypted_payload="ciphertext",
                schema_version=1,
            )
        )
        db.session.commit()
        integration_id = integration.id

    class FakeBrokerAdapter:
        def validate_credentials(self, config):
            assert config["secret_payload"] == {"access_token": "token-1"}
            return {"status": "valid", "message": "ok"}

        def get_account_summary(self, integration):
            assert integration.id == integration_id
            return {"currency": "HKD", "equity": "12345.67"}

        def get_positions(self, integration):
            assert integration.id == integration_id
            return [{"symbol": "00700.HK", "quantity": "100", "market": "hk"}]

    from app.services import integrations as integrations_service

    monkeypatch.setattr(integrations_service, "decrypt_secret_payload", lambda integration: {"access_token": "token-1"})
    monkeypatch.setattr(integrations_service, "get_broker_adapter", lambda provider_key: FakeBrokerAdapter())

    validate_response = client.post(
        f"/api/v1/integrations/{integration_id}/validate",
        headers=_auth_headers(token),
    )
    account_response = client.get(
        f"/api/v1/integrations/{integration_id}/account",
        headers=_auth_headers(token),
    )
    positions_response = client.get(
        f"/api/v1/integrations/{integration_id}/positions",
        headers=_auth_headers(token),
    )

    assert validate_response.status_code == 200
    assert validate_response.json["data"] == {"status": "valid", "message": "ok"}
    assert account_response.status_code == 200
    assert account_response.json["data"] == {"currency": "HKD", "equity": "12345.67"}
    assert positions_response.status_code == 200
    assert positions_response.json["data"] == [{"symbol": "00700.HK", "quantity": "100", "market": "hk"}]
