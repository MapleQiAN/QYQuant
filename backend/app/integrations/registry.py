from dataclasses import dataclass, field


class UnknownIntegrationProviderError(KeyError):
    pass


@dataclass(frozen=True)
class ProviderDefinition:
    key: str
    name: str
    type: str
    mode: str
    capabilities: dict[str, bool] = field(default_factory=dict)
    config_schema: dict[str, object] = field(default_factory=dict)
    is_enabled: bool = True


_PROVIDERS = {
    "joinquant": ProviderDefinition(
        key="joinquant",
        name="JoinQuant",
        type="market_data",
        mode="hosted",
        capabilities={"daily_bars": True, "latest_quote": True},
        config_schema={"fields": []},
    ),
    "longport": ProviderDefinition(
        key="longport",
        name="LongPort",
        type="broker_account",
        mode="hosted",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"fields": ["app_key", "app_secret", "access_token"]},
    ),
    "gmtrade": ProviderDefinition(
        key="gmtrade",
        name="GMTrade",
        type="broker_account",
        mode="hosted",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"fields": ["token"]},
    ),
    "xtquant": ProviderDefinition(
        key="xtquant",
        name="XtQuant",
        type="broker_account",
        mode="local_connector",
        capabilities={"account_summary": True, "positions": True},
        config_schema={"fields": ["account_id", "endpoint"]},
    ),
}


def list_providers() -> list[ProviderDefinition]:
    return list(_PROVIDERS.values())


def get_provider(key: str) -> ProviderDefinition:
    provider = _PROVIDERS.get(key)
    if provider is None:
        raise UnknownIntegrationProviderError(key)
    return provider
