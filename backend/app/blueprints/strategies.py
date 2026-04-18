import os
from pathlib import Path

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import BacktestJob, File, Strategy, StrategyVersion
from ..schemas import StrategyParameterSchema, StrategySchema
from ..services.strategy_import_analysis import (
    StrategyImportAnalysisError,
    analyze_strategy_import,
)
from ..services.ai_strategy_generation import (
    AIStrategyGenerationError,
    generate_strategy_draft,
)
from ..services.strategy_import_confirm import (
    StrategyImportConfirmError,
    confirm_strategy_import,
)
from ..services.strategy_import import StrategyImportError, import_strategy_package
from ..strategy_runtime import StrategyRuntimeError
from ..strategy_runtime.loader import load_strategy_package
from ..utils.response import error_response, ok
from ..utils.time import now_ms

bp = Blueprint("strategies", __name__, url_prefix="/api")


@bp.post("/strategies")
@jwt_required()
def create_strategy():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    name = (payload.get("name") or "").strip()
    symbol = (payload.get("symbol") or "").strip()
    if not name:
        return {"code": 40000, "message": "name_required", "details": None}, 400
    if not symbol:
        return {"code": 40000, "message": "symbol_required", "details": None}, 400

    tags = payload.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    status = payload.get("status") or "draft"
    if status not in {"draft", "running", "paused", "stopped", "completed"}:
        status = "draft"

    strategy = Strategy(
        name=name,
        symbol=symbol,
        status=status,
        source="manual",
        owner_id=user_id,
        returns=0,
        win_rate=0,
        max_drawdown=0,
        tags=tags,
        last_update=now_ms(),
        trades=0,
    )
    db.session.add(strategy)
    db.session.commit()
    return ok(StrategySchema().dump(strategy))


@bp.post("/strategies/import")
@jwt_required()
def import_strategy_legacy():
    user_id = get_jwt_identity()
    incoming = request.files.get("file")
    if not incoming:
        return {"code": 40000, "message": "file_required", "details": None}, 400

    try:
        strategy, version, file_record = import_strategy_package(incoming, owner_id=user_id)
    except StrategyImportError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    return ok(_build_import_payload(strategy, version, file_record))


@bp.get("/strategies/recent")
def recent():
    items = Strategy.query.order_by(Strategy.last_update.desc()).limit(10).all()
    return ok(StrategySchema(many=True).dump(items))


@bp.get("/strategies/<strategy_id>/runtime")
@jwt_required(optional=True)
def runtime_descriptor(strategy_id):
    requested_version = request.args.get("version")
    user_id = get_jwt_identity()

    try:
        loaded = load_strategy_package(strategy_id, requested_version, user_id=user_id)
    except StrategyRuntimeError as exc:
        if exc.message == "strategy_not_found":
            return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)
        if exc.message == "strategy_version_not_found":
            return error_response("STRATEGY_VERSION_NOT_FOUND", "Strategy version not found", 404)
        return {"code": 40000, "message": exc.message, "details": exc.details}, 400

    manifest = loaded.get("manifest") or {}
    entrypoint = manifest.get("entrypoint") or {}
    return ok(
        {
            "strategyId": strategy_id,
            "strategyVersion": loaded.get("version"),
            "name": manifest.get("name"),
            "interface": entrypoint.get("interface") or "event_v1",
            "parameters": manifest.get("parameters") or [],
        }
    )


@bp.get("/v1/strategies/<strategy_id>/parameters")
@jwt_required()
def get_strategy_parameters(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_accessible_strategy(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)
    runtime_strategy_id = strategy.source_strategy_id or strategy.id

    strategy_version = (
        StrategyVersion.query.filter_by(strategy_id=runtime_strategy_id)
        .order_by(StrategyVersion.created_at.desc())
        .first()
    )
    if strategy_version is None:
        return error_response("STRATEGY_VERSION_NOT_FOUND", "Strategy version not found", 404)

    try:
        loaded = load_strategy_package(strategy_id, strategy_version.version, user_id=user_id)
    except StrategyRuntimeError as exc:
        return error_response("STRATEGY_PARAMETERS_UNAVAILABLE", exc.message, 422, details=exc.details)

    parameters = [_normalize_parameter_definition(item) for item in (loaded.get("manifest") or {}).get("parameters") or []]
    return ok(StrategyParameterSchema(many=True).dump(parameters))


@bp.get("/v1/strategies/")
@jwt_required()
def list_strategies():
    user_id = get_jwt_identity()
    page = _int_arg("page", 1, minimum=1)
    per_page = _int_arg("per_page", 20, minimum=1, maximum=100)
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc").lower()

    query = Strategy.query.filter_by(owner_id=user_id).filter(Strategy.deleted_at.is_(None))
    sort_column = _sort_column(sort)
    query = query.order_by(sort_column.desc() if order != "asc" else sort_column.asc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return ok(
        {
            "items": StrategySchema(many=True).dump(items),
            "page": page,
            "perPage": per_page,
            "total": total,
        }
    )

@bp.post("/v1/strategy-imports/analyze")
@jwt_required()
def analyze_strategy_import_v1():
    incoming = request.files.get("file")
    if not incoming:
        return error_response("FILE_REQUIRED", "Strategy source file is required", 400)

    try:
        draft, _, analysis = analyze_strategy_import(incoming, owner_id=get_jwt_identity())
    except StrategyImportAnalysisError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    payload = dict(analysis)
    payload["draftImportId"] = draft.id
    return ok(payload)


@bp.post("/v1/strategy-imports/confirm")
@jwt_required()
def confirm_strategy_import_v1():
    payload = request.get_json() or {}
    draft_import_id = payload.get("draftImportId")
    if not draft_import_id:
        return error_response("DRAFT_IMPORT_ID_REQUIRED", "Import draft id is required", 400)

    try:
        strategy, version, file_record = confirm_strategy_import(
            draft_import_id,
            owner_id=get_jwt_identity(),
            payload=payload,
        )
    except StrategyImportConfirmError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    response_payload = _build_import_payload(strategy, version, file_record)
    response_payload["next"] = f"/strategies/{strategy.id}/parameters"
    return ok(response_payload)


@bp.post("/v1/strategy-ai/generate")
@jwt_required()
def generate_ai_strategy_v1():
    payload = request.get_json() or {}
    integration_id = str(payload.get("integrationId") or "").strip()
    if not integration_id:
        return error_response("INTEGRATION_ID_REQUIRED", "AI integration id is required", 400)

    try:
        result = generate_strategy_draft(
            user_id=get_jwt_identity(),
            integration_id=integration_id,
            messages=payload.get("messages"),
        )
    except AIStrategyGenerationError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    return ok(result)


@bp.delete("/v1/strategies/<strategy_id>")
@jwt_required()
def delete_strategy(strategy_id):
    user_id = get_jwt_identity()
    strategy = Strategy.query.filter_by(id=strategy_id, owner_id=user_id).first()
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    _delete_strategy_assets(strategy)
    db.session.delete(strategy)
    db.session.commit()
    return ok({"deletedId": strategy_id})


@bp.post("/v1/strategies/import")
@jwt_required()
def import_strategy_v1():
    incoming = request.files.get("file")
    if not incoming:
        return error_response("FILE_REQUIRED", "Strategy package is required", 400)

    try:
        strategy, version, file_record = import_strategy_package(incoming, owner_id=get_jwt_identity())
    except StrategyImportError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    payload = _build_import_payload(strategy, version, file_record)
    payload["next"] = f"/strategies/{strategy.id}/parameters"
    return ok(payload)


def _build_import_payload(strategy, version, file_record):
    return {
        "strategy": StrategySchema().dump(strategy),
        "version": {
            "id": version.id,
            "version": version.version,
            "checksum": version.checksum,
            "fileId": file_record.id,
        },
        "file": {
            "id": file_record.id,
            "filename": file_record.filename,
            "size": file_record.size,
            "path": file_record.path,
        },
    }


def _get_accessible_strategy(strategy_id, user_id):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        return None
    if strategy.owner_id not in {None, user_id}:
        return None
    return strategy


def _normalize_parameter_definition(definition):
    raw_type = str(definition.get("type") or "string").lower()
    options = definition.get("options")
    if options is None:
        options = definition.get("enum")

    if raw_type in {"integer", "int"}:
        normalized_type = "int"
    elif raw_type in {"number", "float"}:
        normalized_type = "float"
    elif raw_type == "boolean":
        normalized_type = "enum"
        options = [True, False] if options is None else options
    elif raw_type == "enum" or options is not None:
        normalized_type = "enum"
    else:
        normalized_type = "string"

    return {
        "name": definition.get("name") or definition.get("key"),
        "type": normalized_type,
        "default": definition.get("default"),
        "required": bool(definition.get("required", False)),
        "min": definition.get("min"),
        "max": definition.get("max"),
        "step": definition.get("step"),
        "description": definition.get("description"),
        "options": options,
        "userFacing": definition.get("user_facing") or definition.get("userFacing"),
    }


def _int_arg(name, default, *, minimum=None, maximum=None):
    raw = request.args.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _sort_column(name):
    mapping = {
        "created_at": Strategy.created_at,
        "updated_at": Strategy.updated_at,
        "name": Strategy.name,
    }
    return mapping.get(name, Strategy.created_at)


def _delete_strategy_assets(strategy):
    versions = StrategyVersion.query.filter_by(strategy_id=strategy.id).all()
    file_ids = [version.file_id for version in versions if version.file_id]

    for version in versions:
        db.session.delete(version)

    if file_ids:
        for file_record in File.query.filter(File.id.in_(file_ids)).all():
            _remove_path(file_record.path)
            db.session.delete(file_record)

    if strategy.storage_key and not strategy.source_strategy_id:
        storage_root = Path(os.getenv("STRATEGY_STORAGE_DIR") or Path(__file__).resolve().parents[2] / "storage")
        _remove_path((storage_root / strategy.storage_key).as_posix())

    BacktestJob.query.filter_by(strategy_id=strategy.id).update({"strategy_id": None})


def _remove_path(path):
    if not path:
        return
    candidate = Path(path)
    if candidate.exists() and candidate.is_file():
        candidate.unlink()
