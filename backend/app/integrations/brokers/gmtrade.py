from .base import BrokerAccountAdapter


def _require_fields(payload, field_names):
    missing = [field for field in field_names if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _build_config(config_or_integration):
    if hasattr(config_or_integration, "config_public"):
        config_public = dict(config_or_integration.config_public or {})
        secret_payload = dict(getattr(config_or_integration, "_secret_payload", None) or {})
        return {"config_public": config_public, "secret_payload": secret_payload}
    return {
        "config_public": dict(config_or_integration.get("config_public") or {}),
        "secret_payload": dict(config_or_integration.get("secret_payload") or {}),
    }


class GMTradeBrokerAdapter(BrokerAccountAdapter):
    def __init__(self, client_factory=None):
        self.client_factory = client_factory or self._default_client_factory

    def _default_client_factory(self, _config):
        raise RuntimeError("GMTrade SDK client is not configured")

    def _connect(self, config):
        _require_fields(config["secret_payload"], ["token"])
        _require_fields(config["config_public"], ["account_id"])
        client = self.client_factory(config)
        client.connect(
            config["secret_payload"]["token"],
            config["config_public"]["account_id"],
            endpoint=config["config_public"].get("endpoint"),
        )
        return client

    def validate_credentials(self, config):
        self._connect(_build_config(config))
        return {"status": "valid", "message": "ok"}

    def get_account_summary(self, integration):
        client = self._connect(_build_config(integration))
        return dict(client.get_account_summary() or {})

    def get_positions(self, integration):
        client = self._connect(_build_config(integration))
        return list(client.get_positions() or [])
