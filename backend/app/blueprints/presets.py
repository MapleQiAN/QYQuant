from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import Strategy, StrategyParameterPreset
from ..schemas import StrategyParameterPresetSchema
from ..utils.response import error_response, ok


bp = Blueprint("presets", __name__, url_prefix="/api")


def _get_strategy_for_user(strategy_id, user_id):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        return None
    if strategy.owner_id not in {None, user_id}:
        return None
    return strategy


def _load_owned_preset(strategy_id, preset_id, user_id):
    return StrategyParameterPreset.query.filter_by(
        id=preset_id,
        strategy_id=strategy_id,
        user_id=user_id,
    ).first()


def _validate_payload(payload):
    name = (payload.get("name") or "").strip()
    parameters = payload.get("parameters")

    if not name:
        return None, None, error_response("VALIDATION_ERROR", "name is required", 422)
    if len(name) > 100:
        return None, None, error_response("VALIDATION_ERROR", "name must be at most 100 characters", 422)
    if not isinstance(parameters, dict):
        return None, None, error_response("VALIDATION_ERROR", "parameters must be an object", 422)
    return name, parameters, None


@bp.get("/v1/strategies/<strategy_id>/presets")
@jwt_required()
def list_strategy_presets(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_strategy_for_user(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    presets = (
        StrategyParameterPreset.query.filter_by(strategy_id=strategy.id, user_id=user_id)
        .order_by(StrategyParameterPreset.created_at.desc())
        .all()
    )
    return ok(StrategyParameterPresetSchema(many=True).dump(presets))


@bp.post("/v1/strategies/<strategy_id>/presets")
@jwt_required()
def create_strategy_preset(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_strategy_for_user(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    name, parameters, validation_error = _validate_payload(request.get_json() or {})
    if validation_error is not None:
        return validation_error

    preset = StrategyParameterPreset(
        strategy_id=strategy.id,
        user_id=user_id,
        name=name,
        parameters=parameters,
    )
    db.session.add(preset)
    db.session.commit()
    return ok(StrategyParameterPresetSchema().dump(preset))


@bp.put("/v1/strategies/<strategy_id>/presets/<preset_id>")
@jwt_required()
def update_strategy_preset(strategy_id, preset_id):
    user_id = get_jwt_identity()
    strategy = _get_strategy_for_user(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    preset = _load_owned_preset(strategy.id, preset_id, user_id)
    if preset is None:
        return error_response("PRESET_NOT_FOUND", "Preset not found", 404)

    name, parameters, validation_error = _validate_payload(request.get_json() or {})
    if validation_error is not None:
        return validation_error

    preset.name = name
    preset.parameters = parameters
    db.session.commit()
    return ok(StrategyParameterPresetSchema().dump(preset))


@bp.delete("/v1/strategies/<strategy_id>/presets/<preset_id>")
@jwt_required()
def delete_strategy_preset(strategy_id, preset_id):
    user_id = get_jwt_identity()
    strategy = _get_strategy_for_user(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    preset = _load_owned_preset(strategy.id, preset_id, user_id)
    if preset is None:
        return error_response("PRESET_NOT_FOUND", "Preset not found", 404)

    db.session.delete(preset)
    db.session.commit()
    return ok({"deletedId": preset_id})
