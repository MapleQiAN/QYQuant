from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..services import integrations as integrations_service
from ..utils.response import error_response, ok

bp = Blueprint("integrations", __name__, url_prefix="/api/v1/integrations")


@bp.get("/providers")
@jwt_required()
def list_providers():
    integrations_service.sync_provider_catalog()
    from ..models import IntegrationProvider

    providers = (
        IntegrationProvider.query
        .filter(IntegrationProvider.is_enabled.is_(True))
        .order_by(IntegrationProvider.type.asc(), IntegrationProvider.key.asc())
        .all()
    )
    return ok([integrations_service.serialize_provider(provider) for provider in providers])


@bp.get("")
@jwt_required()
def list_integrations():
    user_id = get_jwt_identity()
    items = integrations_service.list_user_integrations(user_id)
    return ok([integrations_service.serialize_integration(item) for item in items])


@bp.post("")
@jwt_required()
def create_user_integration():
    payload = request.get_json() or {}
    provider_key = str(payload.get("provider_key") or "").strip()
    display_name = str(payload.get("display_name") or "").strip()
    if not provider_key:
        return error_response("VALIDATION_ERROR", "provider_key is required", 422)
    if not display_name:
        return error_response("VALIDATION_ERROR", "display_name is required", 422)

    try:
        integration = integrations_service.create_integration(
            user_id=get_jwt_identity(),
            provider_key=provider_key,
            display_name=display_name,
            config_public=payload.get("config_public") or {},
            secret_payload=payload.get("secret_payload") or {},
        )
    except KeyError:
        return error_response("INTEGRATION_PROVIDER_NOT_FOUND", "Provider not found", 404)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), 422)

    return ok(integrations_service.serialize_integration(integration)), 201


def _integration_or_404(integration_id):
    integration = integrations_service.get_user_integration(integration_id, get_jwt_identity())
    if integration is None:
        return None, error_response("INTEGRATION_NOT_FOUND", "Integration not found", 404)
    return integration, None


@bp.post("/<integration_id>/validate")
@jwt_required()
def validate_integration(integration_id):
    integration, error = _integration_or_404(integration_id)
    if error:
        return error

    adapter = integrations_service.get_broker_adapter(integration.provider_key)
    result = adapter.validate_credentials(
        {
            "config_public": dict(integration.config_public or {}),
            "secret_payload": integrations_service.decrypt_secret_payload(integration),
        }
    )
    integrations_service.mark_validation_result(integration, result)
    return ok(result)


@bp.get("/<integration_id>/account")
@jwt_required()
def get_account(integration_id):
    integration, error = _integration_or_404(integration_id)
    if error:
        return error

    adapter = integrations_service.get_broker_adapter(integration.provider_key)
    integrations_service.attach_secret_payload(integration)
    return ok(adapter.get_account_summary(integration))


@bp.get("/<integration_id>/positions")
@jwt_required()
def get_positions(integration_id):
    integration, error = _integration_or_404(integration_id)
    if error:
        return error

    adapter = integrations_service.get_broker_adapter(integration.provider_key)
    integrations_service.attach_secret_payload(integration)
    return ok(adapter.get_positions(integration))
