import json

from ..extensions import db
from ..integrations.brokers import GMTradeBrokerAdapter, LongPortBrokerAdapter, XtQuantBrokerAdapter
from ..integrations.llm import OpenAICompatibleLLMAdapter
from ..integrations.registry import get_provider, list_providers
from ..models import IntegrationProvider, UserIntegration, UserIntegrationSecret
from ..utils.crypto import decrypt_text, encrypt_text
from ..utils.time import format_beijing_iso, now_utc


class BrokerAdapterNotImplemented:
    def validate_credentials(self, _config):
        return {"status": "unsupported", "message": "Broker adapter is not implemented yet"}

    def get_account_summary(self, _integration):
        return {}

    def get_positions(self, _integration):
        return []


def sync_provider_catalog(session=None):
    session = session or db.session
    for provider in list_providers():
        row = session.get(IntegrationProvider, provider.key)
        if row is None:
            row = IntegrationProvider(
                key=provider.key,
                name=provider.name,
                type=provider.type,
                mode=provider.mode,
                capabilities=provider.capabilities,
                config_schema=provider.config_schema,
                is_enabled=provider.is_enabled,
            )
            session.add(row)
            continue
        row.name = provider.name
        row.type = provider.type
        row.mode = provider.mode
        row.capabilities = provider.capabilities
        row.config_schema = provider.config_schema
        row.is_enabled = provider.is_enabled


def serialize_provider(provider):
    return {
        "key": provider.key,
        "name": provider.name,
        "type": provider.type,
        "mode": provider.mode,
        "capabilities": dict(provider.capabilities or {}),
        "config_schema": dict(provider.config_schema or {}),
        "is_enabled": bool(provider.is_enabled),
    }


def serialize_integration(integration):
    return {
        "id": integration.id,
        "provider_key": integration.provider_key,
        "display_name": integration.display_name,
        "status": integration.status,
        "config_public": dict(integration.config_public or {}),
        "last_validated_at": format_beijing_iso(integration.last_validated_at),
        "last_success_at": format_beijing_iso(integration.last_success_at),
        "last_failure_at": format_beijing_iso(integration.last_failure_at),
        "last_error_message": integration.last_error_message,
        "created_at": format_beijing_iso(integration.created_at),
        "updated_at": format_beijing_iso(integration.updated_at),
    }


def encrypt_secret_payload(secret_payload):
    serialized = json.dumps(secret_payload or {}, sort_keys=True)
    return encrypt_text(serialized)


def decrypt_secret_payload(integration, session=None):
    session = session or db.session
    secret = session.get(UserIntegrationSecret, integration.id)
    if secret is None:
        return {}
    return json.loads(decrypt_text(secret.encrypted_payload))


def _required_config_fields(config_schema, key):
    fields = (config_schema or {}).get(key)
    if isinstance(fields, list):
        return [str(field) for field in fields]
    if key == "secret_fields":
        legacy_fields = (config_schema or {}).get("fields")
        if isinstance(legacy_fields, list):
            return [str(field) for field in legacy_fields]
    return []


def create_integration(*, user_id, provider_key, display_name, config_public=None, secret_payload=None, session=None):
    session = session or db.session
    sync_provider_catalog(session)
    provider = get_provider(provider_key)
    config_schema = provider.config_schema or {}
    required_public_fields = _required_config_fields(config_schema, "public_fields")
    required_secret_fields = _required_config_fields(config_schema, "secret_fields")
    config_public = config_public or {}
    secret_payload = secret_payload or {}
    missing_public_fields = [field for field in required_public_fields if not config_public.get(field)]
    if missing_public_fields:
        raise ValueError(f"Missing required public fields: {', '.join(missing_public_fields)}")
    missing_secret_fields = [field for field in required_secret_fields if not secret_payload.get(field)]
    if missing_secret_fields:
        raise ValueError(f"Missing required secret fields: {', '.join(missing_secret_fields)}")

    integration = UserIntegration(
        user_id=user_id,
        provider_key=provider_key,
        display_name=display_name,
        status="active",
        config_public=config_public,
    )
    session.add(integration)
    session.flush()

    session.add(
        UserIntegrationSecret(
            integration_id=integration.id,
            encrypted_payload=encrypt_secret_payload(secret_payload),
            schema_version=1,
        )
    )
    session.commit()
    return integration


def list_user_integrations(user_id, session=None):
    session = session or db.session
    return (
        session.query(UserIntegration)
        .filter(
            UserIntegration.user_id == user_id,
            UserIntegration.deleted_at.is_(None),
        )
        .order_by(UserIntegration.created_at.desc(), UserIntegration.id.desc())
        .all()
    )


def get_user_integration(integration_id, user_id, session=None):
    session = session or db.session
    return (
        session.query(UserIntegration)
        .filter(
            UserIntegration.id == integration_id,
            UserIntegration.user_id == user_id,
            UserIntegration.deleted_at.is_(None),
        )
        .first()
    )


def mark_validation_result(integration, result, session=None):
    session = session or db.session
    status = result.get("status") or "invalid"
    integration.last_validated_at = now_utc()
    if status == "valid":
        integration.last_success_at = integration.last_validated_at
        integration.last_error_message = None
    else:
        integration.last_failure_at = integration.last_validated_at
        integration.last_error_message = result.get("message")
    session.commit()


def attach_secret_payload(integration, session=None):
    if session is None:
        integration._secret_payload = decrypt_secret_payload(integration)
    else:
        integration._secret_payload = decrypt_secret_payload(integration, session=session)
    return integration


def get_broker_adapter(_provider_key):
    mapping = {
        "longport": LongPortBrokerAdapter,
        "gmtrade": GMTradeBrokerAdapter,
        "xtquant": XtQuantBrokerAdapter,
    }
    adapter_cls = mapping.get(_provider_key)
    if adapter_cls is None:
        return BrokerAdapterNotImplemented()
    return adapter_cls()


def get_adapter_for_provider(provider_key):
    provider = get_provider(provider_key)
    if provider.type == "broker_account":
        return get_broker_adapter(provider_key)
    if provider.type == "llm":
        mapping = {
            "openai_compatible": OpenAICompatibleLLMAdapter,
        }
        adapter_cls = mapping.get(provider_key)
        if adapter_cls:
            return adapter_cls()
    return _UnsupportedAdapter()


class _UnsupportedAdapter:
    def validate_credentials(self, _config):
        return {"status": "unsupported", "message": "Validation not implemented for this provider type"}

    def get_account_summary(self, _integration):
        return {}

    def get_positions(self, _integration):
        return []
