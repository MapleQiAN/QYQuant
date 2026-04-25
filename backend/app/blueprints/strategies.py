import io
import json
import os
import shutil
import uuid
import zipfile
from pathlib import Path

from flask import request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from qysp.builder import build_package

from ..extensions import db
from ..models import BacktestJob, File, Strategy, StrategyImportDraft, StrategyVersion
from ..schemas import StrategyParameterSchema, StrategySchema
from ..services.strategy_import_analysis import (
    StrategyImportAnalysisError,
    analyze_strategy_import,
)
from ..services.ai_strategy_generation import (
    AIStrategyGenerationError,
    generate_strategy_draft,
)
from ..services.intent_classifier import (
    IntentClassificationError,
    classify_intent,
)
from ..services.risk_profile import build_risk_profile
from ..services.strategy_summary import format_strategy_summary
from ..services.optimizer import optimize_parameters
from ..services.user_facing_generator import generate_user_facing, UserFacingGenerationError
from ..services.strategy_import_confirm import (
    StrategyImportConfirmError,
    confirm_strategy_import,
    _resolve_source_and_manifest,
    _build_manifest,
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
            locale=str(payload.get("locale") or "en").strip(),
        )
    except AIStrategyGenerationError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    return ok(result)


@bp.post("/v1/strategy-ai/export")
@jwt_required()
def export_strategy():
    payload = request.get_json() or {}
    draft_import_id = payload.get("draftImportId")
    if not draft_import_id:
        return error_response("DRAFT_IMPORT_ID_REQUIRED", "Import draft id is required", 400)

    export_format = str(payload.get("format") or "qys").strip().lower()
    if export_format not in ("qys", "py"):
        return error_response("INVALID_FORMAT", "Format must be 'qys' or 'py'", 400)

    user_id = get_jwt_identity()
    draft = db.session.get(StrategyImportDraft, draft_import_id)
    if draft is None or draft.owner_id != user_id:
        return error_response("DRAFT_NOT_FOUND", "Import draft not found", 404)

    source_file = db.session.get(File, draft.source_file_id)
    if source_file is None or not source_file.path:
        return error_response("SOURCE_NOT_FOUND", "Source file not found", 404)

    raw_payload = Path(source_file.path).read_bytes()

    try:
        source_text, base_manifest = _resolve_source_and_manifest(
            raw_payload, draft.source_type, "src/strategy.py"
        )
    except StrategyImportConfirmError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    metadata = payload.get("metadata") or {}
    parameter_definitions = payload.get("parameterDefinitions") or []
    entrypoint_candidates = draft.analysis_payload.get("entrypointCandidates") if isinstance(draft.analysis_payload, dict) else []
    selected_callable = "on_bar"
    selected_interface = "event_v1"
    if entrypoint_candidates:
        selected_callable = entrypoint_candidates[0].get("callable", "on_bar")
        selected_interface = entrypoint_candidates[0].get("interface", "event_v1")

    if export_format == "py":
        buffer = io.BytesIO(source_text.encode("utf-8"))
        filename = _slugify(metadata.get("name") or "strategy") + ".py"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype="text/x-python")

    manifest = _build_manifest(
        base_manifest=base_manifest,
        metadata=metadata,
        parameter_definitions=parameter_definitions,
        selected_callable=selected_callable,
        selected_interface=selected_interface,
    )

    logic_explanation = (metadata.get("logicExplanation") or "")
    risk_rules = (metadata.get("riskRules") or "")
    suitable_market = (metadata.get("suitableMarket") or "")
    risk_level = (metadata.get("riskLevel") or "")
    readme_parts = [
        f"# {manifest.get('name', 'Strategy')}",
        "",
        manifest.get("description", ""),
        "",
        "## Strategy Logic",
        logic_explanation or "See code comments.",
        "",
        "## Risk Management",
        risk_rules or "Stop-loss and take-profit included.",
        "",
        "## Suitable Market",
        suitable_market or "General market conditions.",
    ]
    if risk_level:
        readme_parts.extend(["", f"**Risk Level**: {risk_level}"])
    readme_text = "\n".join(readme_parts)

    temp_root = Path(os.getenv("STRATEGY_STORAGE_DIR", str(Path(__file__).resolve().parents[2] / "storage"))) / "_tmp" / f"export-{uuid.uuid4().hex}"
    project_dir = temp_root / "project"
    project_src_dir = project_dir / "src"
    try:
        project_src_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "strategy.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (project_src_dir / "strategy.py").write_text(source_text, encoding="utf-8")
        (project_dir / "README.md").write_text(readme_text, encoding="utf-8")

        built_path = temp_root / "built.qys"
        build_package(project_dir, output=built_path)
        package_bytes = built_path.read_bytes()

        filename = _slugify(manifest.get("name", "strategy")) + ".qys"
        return send_file(
            io.BytesIO(package_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip",
        )
    except Exception as exc:
        return error_response("EXPORT_FAILED", str(exc), 500)
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)


def _slugify(name):
    import re
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-") or "strategy"


@bp.post("/v1/strategy-ai/classify")
@jwt_required()
def classify_strategy_intent():
    payload = request.get_json() or {}
    integration_id = str(payload.get("integrationId") or "").strip()
    if not integration_id:
        return error_response("INTEGRATION_ID_REQUIRED", "AI integration id is required", 400)
    description = str(payload.get("description") or "").strip()
    if not description:
        return error_response("DESCRIPTION_REQUIRED", "Strategy description is required", 400)

    try:
        result = classify_intent(
            user_id=get_jwt_identity(),
            integration_id=integration_id,
            description=description,
        )
    except IntentClassificationError as exc:
        return error_response(exc.code, exc.message, exc.status, details=exc.details)

    return ok(result)


@bp.post("/v1/strategy-risk-profile")
@jwt_required()
def build_risk_profile_endpoint():
    payload = request.get_json() or {}
    required_fields = ("max_single_loss_pct", "position_ratio", "drawdown_tolerance",
                       "consecutive_loss_patience", "style")
    missing = [f for f in required_fields if f not in payload and f not in (payload or {})]
    if missing:
        return error_response("FIELDS_REQUIRED", f"Missing fields: {', '.join(missing)}", 400)

    profile = build_risk_profile(
        max_single_loss_pct=payload.get("max_single_loss_pct", 5.0),
        position_ratio=payload.get("position_ratio", 0.5),
        drawdown_tolerance=payload.get("drawdown_tolerance", "medium"),
        consecutive_loss_patience=payload.get("consecutive_loss_patience", 3),
        style=payload.get("style", "balanced"),
    )
    from ..services.risk_profile import risk_profile_to_generator_context
    return ok({
        "profile": profile.to_dict(),
        "generatorContext": risk_profile_to_generator_context(profile),
    })


@bp.post("/v1/strategy-ai/summary")
@jwt_required()
def strategy_summary_endpoint():
    payload = request.get_json() or {}
    integration_id = str(payload.get("integrationId") or "").strip()
    if not integration_id:
        return error_response("INTEGRATION_ID_REQUIRED", "AI integration id is required", 400)
    code = str(payload.get("code") or "").strip()
    if not code:
        return error_response("CODE_REQUIRED", "Strategy code is required", 400)

    result = format_strategy_summary(
        user_id=get_jwt_identity(),
        integration_id=integration_id,
        code=code,
        parameters=payload.get("parameters") or [],
    )
    return ok(result)


@bp.post("/v1/strategies/<strategy_id>/optimize")
@jwt_required()
def optimize_strategy_parameters(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_accessible_strategy(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    payload = request.get_json() or {}
    level = payload.get("level", "standard")
    if level not in ("quick", "standard", "deep"):
        level = "standard"

    try:
        result = optimize_parameters(
            strategy_id=strategy_id,
            strategy_version=payload.get("strategyVersion"),
            parameters=payload.get("parameters", []),
            symbol=payload.get("symbol", strategy.symbol),
            interval=payload.get("interval"),
            limit=payload.get("limit", 500),
            start_time=payload.get("startTime"),
            end_time=payload.get("endTime"),
            data_source=payload.get("dataSource"),
            user_id=user_id,
            level=level,
            risk_style=payload.get("riskStyle", "balanced"),
        )
    except Exception as exc:
        return error_response("OPTIMIZATION_FAILED", str(exc), 500)

    return ok({
        "topResults": result.top_results,
        "overfittingRisk": result.overfitting_risk,
        "searchSpaceSize": result.search_space_size,
        "evaluations": result.evaluations,
    })


@bp.post("/v1/strategy-ai/user-facing")
@jwt_required()
def generate_user_facing_endpoint():
    payload = request.get_json() or {}
    integration_id = str(payload.get("integrationId") or "").strip()
    if not integration_id:
        return error_response("INTEGRATION_ID_REQUIRED", "AI integration id is required", 400)
    parameters = payload.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        return error_response("PARAMETERS_REQUIRED", "Parameters list is required", 400)

    result = generate_user_facing(
        user_id=get_jwt_identity(),
        integration_id=integration_id,
        parameters=parameters,
    )
    return ok({"parameters": result})


@bp.post("/v1/strategies/code")
@jwt_required()
def create_strategy_with_code():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    code = (payload.get("code") or "").strip()
    name = (payload.get("name") or "").strip()
    symbol = (payload.get("symbol") or "").strip()
    if not code:
        return error_response("CODE_REQUIRED", "Strategy code is required", 400)
    if not name:
        return error_response("NAME_REQUIRED", "Strategy name is required", 400)
    if not symbol:
        return error_response("SYMBOL_REQUIRED", "Symbol is required", 400)

    tags = payload.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    storage_root = Path(os.getenv("STRATEGY_STORAGE_DIR") or Path(__file__).resolve().parents[2] / "storage")
    storage_key = f"editor/{user_id}/{uuid.uuid4().hex}"
    code_path = storage_root / storage_key / "strategy.py"
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(code, encoding="utf-8")

    strategy = Strategy(
        name=name,
        symbol=symbol,
        status="draft",
        source="editor",
        owner_id=user_id,
        storage_key=storage_key,
        description=payload.get("description"),
        category=payload.get("category"),
        tags=tags,
        returns=0,
        win_rate=0,
        max_drawdown=0,
        last_update=now_ms(),
        trades=0,
    )
    db.session.add(strategy)
    db.session.commit()
    return ok(StrategySchema().dump(strategy))


@bp.get("/v1/strategies/<strategy_id>/code")
@jwt_required()
def get_strategy_code(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_accessible_strategy(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    if not strategy.storage_key:
        return error_response("CODE_NOT_AVAILABLE", "No source code available for this strategy", 404)

    storage_root = Path(os.getenv("STRATEGY_STORAGE_DIR") or Path(__file__).resolve().parents[2] / "storage")
    code_path = storage_root / strategy.storage_key / "strategy.py"
    if not code_path.exists():
        return error_response("CODE_NOT_AVAILABLE", "Source file not found", 404)

    code = code_path.read_text(encoding="utf-8")
    return ok({"code": code, "filename": "strategy.py"})


@bp.put("/v1/strategies/<strategy_id>/code")
@jwt_required()
def update_strategy_code(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_accessible_strategy(strategy_id, user_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    payload = request.get_json() or {}
    code = payload.get("code")
    if code is not None:
        if not strategy.storage_key:
            storage_root = Path(os.getenv("STRATEGY_STORAGE_DIR") or Path(__file__).resolve().parents[2] / "storage")
            storage_key = f"editor/{user_id}/{uuid.uuid4().hex}"
            strategy.storage_key = storage_key
            code_path = storage_root / storage_key / "strategy.py"
            code_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            storage_root = Path(os.getenv("STRATEGY_STORAGE_DIR") or Path(__file__).resolve().parents[2] / "storage")
            code_path = storage_root / strategy.storage_key / "strategy.py"
        code_path.write_text(code, encoding="utf-8")

    metadata = payload.get("metadata")
    if metadata and isinstance(metadata, dict):
        if "name" in metadata:
            strategy.name = metadata["name"]
        if "description" in metadata:
            strategy.description = metadata["description"]
        if "category" in metadata:
            strategy.category = metadata["category"]
        if "tags" in metadata:
            strategy.tags = metadata["tags"]

    strategy.last_update = now_ms()
    db.session.commit()
    return ok({"id": strategy.id, "updatedAt": strategy.last_update})


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
