from .base import BrokerAccountAdapter


def _require_fields(payload, field_names):
    missing = [field for field in field_names if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _build_config(config_or_integration):
    return {
        "config_public": dict(getattr(config_or_integration, "config_public", None) or config_or_integration.get("config_public") or {}),
        "secret_payload": dict(getattr(config_or_integration, "_secret_payload", None) or config_or_integration.get("secret_payload") or {}),
    }


class LongPortBrokerAdapter(BrokerAccountAdapter):
    def __init__(self, client_factory=None):
        self.client_factory = client_factory or self._default_client_factory

    def _default_client_factory(self, _config):
        raise RuntimeError("LongPort SDK client is not configured")

    def validate_credentials(self, config):
        normalized = _build_config(config)
        _require_fields(normalized["secret_payload"], ["app_key", "app_secret", "access_token"])
        client = self.client_factory(normalized)
        client.get_account_balance()
        return {"status": "valid", "message": "ok"}

    def get_account_summary(self, integration):
        client = self.client_factory(_build_config(integration))
        balance = client.get_account_balance()
        return {
            "currency": balance.get("currency"),
            "cash": balance.get("total_cash"),
            "equity": balance.get("net_assets"),
        }

    def get_positions(self, integration):
        client = self.client_factory(_build_config(integration))
        return list(client.get_positions() or [])
