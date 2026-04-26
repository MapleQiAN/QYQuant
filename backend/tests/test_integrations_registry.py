import pytest


def test_registry_lists_market_data_and_broker_providers():
    from app.integrations.registry import list_providers

    providers = list_providers()
    keys = {provider.key for provider in providers}

    assert "joinquant" in keys
    assert "longport" in keys


def test_registry_resolves_provider_metadata_by_key():
    from app.integrations.registry import get_provider

    provider = get_provider("longport")

    assert provider.key == "longport"
    assert provider.type == "broker_account"
    assert provider.mode in {"hosted", "local_connector"}
    assert provider.capabilities["positions"] is True
    assert provider.capabilities["orders"] is False


def test_registry_rejects_unknown_provider():
    from app.integrations.registry import UnknownIntegrationProviderError, get_provider

    with pytest.raises(UnknownIntegrationProviderError):
        get_provider("missing-provider")
