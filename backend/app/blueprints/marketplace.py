import uuid
from datetime import timedelta
from pathlib import Path

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, File, Report, Strategy, StrategyVersion, User
from ..schemas import StrategySchema
from ..services.notifications import create_notification
from ..utils.audit import log_audit
from ..utils.response import error_response, ok
from ..utils.storage import read_json
from ..utils.time import format_beijing_iso_ms, now_ms, now_utc

bp = Blueprint("marketplace", __name__, url_prefix="/api/v1/marketplace")
BACKTEST_CONFIGURE_PATH = "/backtest/configure"
ALLOWED_MARKETPLACE_CATEGORIES = {
    "trend-following",
    "mean-reversion",
    "momentum",
    "multi-indicator",
    "other",
}
REQUIRED_DISPLAY_METRICS = {"sharpe_ratio", "max_drawdown", "total_return"}


@bp.get("/strategies")
def list_marketplace_strategies():
    featured = _bool_arg("featured", default=False)
    tag = (request.args.get("tag") or "").strip().lower()
    search_term = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    verified = _bool_arg("verified", default=False)
    annual_return_gte = _float_arg("annual_return_gte")
    max_drawdown_lte = _float_arg("max_drawdown_lte")
    page = _int_arg("page", default=1, minimum=1)
    page_size = _int_arg("page_size", default=20, minimum=1, maximum=100)

    if tag == "onboarding":
        _ensure_onboarding_strategy()
        items = (
            Strategy.query
            .filter(Strategy.owner_id.is_(None), _marketplace_visibility_clause())
            .order_by(Strategy.last_update.desc(), Strategy.created_at.desc())
            .all()
        )
        items = [
            item for item in items
            if any(str(entry).strip().lower() == tag for entry in (item.tags or []))
        ]
        return ok(StrategySchema(many=True).dump(items))

    base_query = (
        db.session.query(Strategy, User)
        .outerjoin(User, Strategy.owner_id == User.id)
        .filter(_marketplace_visibility_clause())
    )

    if featured:
        query = (
            base_query
            .filter(Strategy.is_featured.is_(True))
            .order_by(Strategy.last_update.desc(), Strategy.created_at.desc(), Strategy.id.desc())
        )
        total = query.count()
        items = query.limit(6).all()
        return ok(
            [strategy.to_card_dict(author=author) for strategy, author in items],
            meta={"total": total, "page": 1, "page_size": 6},
        )

    query, rank_expr = _apply_marketplace_filters(
        base_query,
        search_term=search_term,
        category=category,
        verified=verified,
        annual_return_gte=annual_return_gte,
        max_drawdown_lte=max_drawdown_lte,
    )
    if rank_expr is not None:
        query = query.order_by(rank_expr.desc(), Strategy.last_update.desc(), Strategy.created_at.desc(), Strategy.id.desc())
    else:
        query = query.order_by(Strategy.last_update.desc(), Strategy.created_at.desc(), Strategy.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        [strategy.to_card_dict(author=author) for strategy, author in items],
        meta={"total": total, "page": page, "page_size": page_size},
    )


@bp.get("/strategies/<strategy_id>")
@jwt_required(optional=True)
def get_marketplace_strategy_detail(strategy_id):
    user_id = get_jwt_identity()
    row = _get_public_strategy_with_author(strategy_id)
    if row is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    strategy, author = row
    imported_strategy = _find_imported_strategy(user_id, strategy)
    author_payload = {
        "nickname": getattr(author, "nickname", None) or "QYQuant",
        "avatar_url": getattr(author, "avatar_url", None) or "",
    }
    payload = {
        "id": strategy.id,
        "title": strategy.title or strategy.name,
        "description": strategy.description,
        "category": strategy.category,
        "tags": strategy.tags or [],
        "display_metrics": strategy.display_metrics or {},
        "is_verified": bool(strategy.is_verified),
        "created_at": format_beijing_iso_ms(strategy.created_at),
        "author": author_payload,
        "already_imported": imported_strategy is not None,
        "imported_strategy_id": imported_strategy.id if imported_strategy else None,
        "has_equity_curve": _find_latest_completed_job(strategy.id) is not None,
        "can_report": bool(user_id and strategy.owner_id != user_id),
    }
    return ok(payload)


@bp.get("/strategies/<strategy_id>/equity-curve")
def get_marketplace_strategy_equity_curve(strategy_id):
    strategy = _get_public_strategy(strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    job = _find_latest_completed_job(strategy.id)
    if job is None or not job.result_storage_key:
        return error_response("EQUITY_CURVE_NOT_FOUND", "Equity curve not found", 404)

    try:
        raw_points = read_json(f"{job.result_storage_key}/equity_curve.json")
    except FileNotFoundError:
        return error_response("EQUITY_CURVE_NOT_FOUND", "Equity curve not found", 404)

    dates, values = _extract_equity_curve(raw_points)
    return ok({"dates": dates, "values": values})


@bp.post("/strategies")
@jwt_required()
def publish_marketplace_strategy():
    user_id = get_jwt_identity()
    payload = request.get_json() or {}
    strategy_id = (payload.get("strategy_id") or "").strip()
    if not strategy_id:
        return error_response("STRATEGY_ID_REQUIRED", "Strategy id is required", 422)

    strategy = Strategy.query.filter_by(id=strategy_id).first()
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)
    if strategy.owner_id != user_id:
        return error_response("STRATEGY_FORBIDDEN", "Strategy does not belong to current user", 403)
    if strategy.review_status in {"pending", "approved"}:
        return error_response("STRATEGY_ALREADY_SUBMITTED", "Strategy is already pending review", 409)

    validation_error = _validate_publish_payload(payload)
    if validation_error is not None:
        return validation_error

    if _find_latest_completed_job(strategy.id) is None:
        return error_response("STRATEGY_BACKTEST_REQUIRED", "A completed backtest is required before publishing", 422)

    strategy.title = payload["title"].strip()
    strategy.description = payload["description"].strip()
    strategy.tags = [str(tag).strip() for tag in payload["tags"] if str(tag).strip()]
    strategy.category = payload["category"].strip()
    strategy.display_metrics = dict(payload["display_metrics"])
    strategy.review_status = "pending"
    strategy.updated_at = now_ms()
    strategy.last_update = now_ms()

    create_notification(
        user_id=user_id,
        type="strategy_review_submitted",
        title="Strategy submitted for review",
        content="Your strategy has been submitted for marketplace review.",
    )
    log_audit(
        operator_id=user_id,
        action="marketplace_strategy_submitted",
        target_type="strategy",
        target_id=strategy.id,
        details={
            "title": strategy.title,
            "category": strategy.category,
            "tags": strategy.tags,
            "display_metrics": strategy.display_metrics,
        },
    )
    db.session.commit()
    return ok({"strategy_id": strategy.id, "review_status": strategy.review_status})


@bp.post("/strategies/<strategy_id>/import")
@jwt_required()
def import_marketplace_strategy(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_public_strategy(strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    existing = _find_imported_strategy(user_id, strategy)
    if existing is not None:
        return error_response("ALREADY_IMPORTED", "Strategy already imported", 409)

    imported_strategy = Strategy(
        name=strategy.name,
        title=strategy.title or strategy.name,
        symbol=strategy.symbol,
        status="draft",
        description=strategy.description,
        category=strategy.category,
        source="marketplace",
        source_strategy_id=strategy.id,
        tags=list(strategy.tags or []),
        owner_id=user_id,
        storage_key=strategy.storage_key,
        is_verified=strategy.is_verified,
        last_update=now_ms(),
        updated_at=now_ms(),
        created_at=now_ms(),
        returns=0,
        win_rate=0,
        max_drawdown=0,
        trades=0,
    )
    db.session.add(imported_strategy)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("ALREADY_IMPORTED", "Strategy already imported", 409)

    return ok(
        {
            "strategy_id": imported_strategy.id,
            "redirect_to": f"{BACKTEST_CONFIGURE_PATH}?strategy_id={imported_strategy.id}",
        }
    )


@bp.get("/strategies/<strategy_id>/import-status")
@jwt_required()
def get_marketplace_import_status(strategy_id):
    user_id = get_jwt_identity()
    strategy = _get_public_strategy(strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    imported_strategy = _find_imported_strategy(user_id, strategy)
    return ok(
        {
            "imported": imported_strategy is not None,
            "user_strategy_id": imported_strategy.id if imported_strategy else None,
        }
    )


@bp.get("/strategies/<strategy_id>/publish-status")
@jwt_required()
def get_marketplace_publish_status(strategy_id):
    user_id = get_jwt_identity()
    strategy = Strategy.query.filter_by(id=strategy_id).first()
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)
    if strategy.owner_id != user_id:
        return error_response("STRATEGY_FORBIDDEN", "Strategy does not belong to current user", 403)

    return ok({"review_status": strategy.review_status, "is_public": bool(strategy.is_public)})


@bp.post("/strategies/<strategy_id>/report")
@jwt_required()
def report_marketplace_strategy(strategy_id):
    reporter_id = get_jwt_identity()
    strategy = _get_public_strategy(strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    if strategy.owner_id == reporter_id:
        return error_response("CANNOT_REPORT_OWN_STRATEGY", "Cannot report your own strategy", 400)

    payload = request.get_json() or {}
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        return error_response("REPORT_REASON_REQUIRED", "Report reason is required", 422)
    if len(reason) < 10 or len(reason) > 500:
        return error_response("REPORT_REASON_INVALID", "Report reason must be between 10 and 500 characters", 422)

    duplicate_cutoff = now_utc() - timedelta(hours=24)
    duplicate_report = (
        Report.query
        .filter(
            Report.reporter_id == reporter_id,
            Report.strategy_id == strategy_id,
            Report.created_at >= duplicate_cutoff,
        )
        .order_by(Report.created_at.desc())
        .first()
    )
    if duplicate_report is not None:
        return error_response(
            "REPORT_ALREADY_SUBMITTED",
            "You have already reported this strategy within 24 hours",
            409,
        )

    report = Report(
        reporter_id=reporter_id,
        strategy_id=strategy_id,
        reason=reason,
        status="pending",
    )
    db.session.add(report)
    log_audit(
        operator_id=reporter_id,
        action="strategy_report_submitted",
        target_type="strategy",
        target_id=strategy_id,
        details={"report_id": report.id, "reason": reason},
    )
    db.session.commit()
    return ok({"report_id": report.id}), 201


def _bool_arg(name, *, default=False):
    raw = request.args.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _int_arg(name, *, default, minimum=None, maximum=None):
    raw = request.args.get(name)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _float_arg(name):
    raw = request.args.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _validate_publish_payload(payload):
    title = payload.get("title")
    description = payload.get("description")
    tags = payload.get("tags")
    category = payload.get("category")
    display_metrics = payload.get("display_metrics")

    if not isinstance(title, str) or not title.strip():
        return error_response("TITLE_REQUIRED", "Title is required", 422)
    if len(title.strip()) > 200:
        return error_response("TITLE_TOO_LONG", "Title must be 200 characters or fewer", 422)
    if not isinstance(description, str) or not description.strip():
        return error_response("DESCRIPTION_REQUIRED", "Description is required", 422)
    if not isinstance(tags, list) or not [str(tag).strip() for tag in tags if str(tag).strip()]:
        return error_response("TAGS_REQUIRED", "At least one tag is required", 422)
    if not isinstance(category, str) or category.strip() not in ALLOWED_MARKETPLACE_CATEGORIES:
        return error_response("CATEGORY_INVALID", "Category is invalid", 422)
    if not isinstance(display_metrics, dict):
        return error_response("DISPLAY_METRICS_REQUIRED", "Display metrics are required", 422)
    missing_metrics = sorted(REQUIRED_DISPLAY_METRICS.difference(display_metrics.keys()))
    if missing_metrics:
        return error_response(
            "DISPLAY_METRICS_INVALID",
            "Display metrics are missing required keys",
            422,
            details={"missing": missing_metrics},
        )
    return None


def _apply_marketplace_filters(query, *, search_term, category, verified, annual_return_gte, max_drawdown_lte):
    rank_expr = None

    if search_term:
        query_expr = db.func.plainto_tsquery("chinese", search_term)
        title_vector = _search_vector_for_column(Strategy.title_tsv, Strategy.title)
        description_vector = _search_vector_for_column(Strategy.description_tsv, Strategy.description)
        query = query.filter(
            db.or_(
                title_vector.op("@@")(query_expr),
                description_vector.op("@@")(query_expr),
            )
        )
        rank_expr = db.func.ts_rank(title_vector, query_expr) + db.func.ts_rank(description_vector, query_expr)

    if category:
        query = query.filter(Strategy.category == category)

    if verified:
        query = query.filter(Strategy.is_verified.is_(True))

    if annual_return_gte is not None:
        annual_return_text = _json_metric_text("annual_return")
        annual_return_expr = db.cast(annual_return_text, db.Float)
        query = query.filter(
            annual_return_text.isnot(None),
            annual_return_expr >= annual_return_gte,
        )

    if max_drawdown_lte is not None:
        max_drawdown_text = _json_metric_text("max_drawdown")
        max_drawdown_expr = db.cast(max_drawdown_text, db.Float)
        # Product copy is expressed as positive percentages, while storage uses negative values.
        query = query.filter(
            max_drawdown_text.isnot(None),
            db.func.abs(max_drawdown_expr) <= max_drawdown_lte,
        )

    raw_tags = request.args.getlist("tags")
    if raw_tags:
        requested_tags = [tag.strip() for tag in raw_tags if tag.strip()]
        if requested_tags:
            tags_expr = db.cast(Strategy.tags, JSONB)
            tag_filters = [tags_expr.contains([tag]) for tag in requested_tags]
            query = query.filter(db.or_(*tag_filters))

    return query, rank_expr


def _search_vector_for_column(stored_vector, source_column):
    return db.func.coalesce(
        stored_vector,
        db.func.to_tsvector("chinese", db.func.coalesce(source_column, "")),
    )


def _json_metric_text(metric_name):
    return db.cast(Strategy.display_metrics, JSONB).op("->>")(metric_name)


def _get_public_strategy(strategy_id):
    return (
        Strategy.query
        .filter(Strategy.id == strategy_id, _marketplace_visibility_clause())
        .first()
    )


def _get_public_strategy_with_author(strategy_id):
    return (
        db.session.query(Strategy, User)
        .outerjoin(User, Strategy.owner_id == User.id)
        .filter(Strategy.id == strategy_id, _marketplace_visibility_clause())
        .first()
    )


def _find_latest_completed_job(strategy_id):
    return (
        BacktestJob.query
        .filter(
            BacktestJob.strategy_id == strategy_id,
            BacktestJob.status == BacktestJobStatus.COMPLETED.value,
            BacktestJob.result_storage_key.isnot(None),
        )
        .order_by(BacktestJob.completed_at.desc(), BacktestJob.created_at.desc())
        .first()
    )


def _extract_equity_curve(raw_points):
    if isinstance(raw_points, dict):
        dates = raw_points.get("dates") or []
        values = raw_points.get("values") or []
        return dates, values

    dates = []
    values = []
    for point in raw_points or []:
        timestamp = point.get("timestamp") if isinstance(point, dict) else None
        equity = point.get("equity") if isinstance(point, dict) else None
        if timestamp is None or equity is None:
            continue
        dates.append(timestamp)
        values.append(equity)
    return dates, values


def _find_imported_strategy(user_id, marketplace_strategy):
    if not user_id:
        return None

    return (
        Strategy.query
        .filter(
            Strategy.owner_id == user_id,
            Strategy.source == "marketplace",
            Strategy.source_strategy_id == marketplace_strategy.id,
        )
        .order_by(Strategy.created_at.desc())
        .first()
    )


_onboarding_seeded = False


def _onboarding_package_path():
    return Path(__file__).resolve().parents[2] / "strategy_store" / "GoldStepByStep.qys"


def _ensure_onboarding_strategy():
    global _onboarding_seeded
    if _onboarding_seeded:
        return
    existing = Strategy.query.filter(Strategy.owner_id.is_(None), _marketplace_visibility_clause()).all()
    if any(any(str(tag).strip().lower() == "onboarding" for tag in (item.tags or [])) for item in existing):
        _onboarding_seeded = True
        return

    package_path = _onboarding_package_path()
    if not package_path.exists():
        return

    strategy_id = "onboarding-gold-step"
    file_id = "onboarding-gold-step-file"
    version = "1.0.0"

    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        strategy = Strategy(
            id=strategy_id,
            name="Gold Step-By-Step",
            title="Gold Step-By-Step",
            symbol="XAUUSD",
            status="running",
            description="Default onboarding strategy for the guided first backtest.",
            category="beginner",
            source="seed",
            returns=0,
            win_rate=0,
            max_drawdown=0,
            tags=["onboarding", "gold", "guided"],
            trades=0,
            owner_id=None,
            is_public=True,
            is_featured=False,
            is_verified=True,
            review_status="approved",
            display_metrics={
                "totalReturn": 0,
                "maxDrawdown": 0,
                "sharpeRatio": 0,
                "winRate": 0,
            },
            storage_key=f"strategy_store/{package_path.name}",
            last_update=now_ms(),
            updated_at=now_ms(),
        )
        db.session.add(strategy)
    else:
        strategy.tags = list({*(strategy.tags or []), "onboarding", "gold", "guided"})
        strategy.owner_id = None
        strategy.title = strategy.title or "Gold Step-By-Step"
        strategy.is_public = True
        strategy.is_featured = False
        strategy.is_verified = True
        strategy.review_status = "approved"
        strategy.display_metrics = strategy.display_metrics or {
            "totalReturn": 0,
            "maxDrawdown": 0,
            "sharpeRatio": 0,
            "winRate": 0,
        }
        strategy.storage_key = f"strategy_store/{package_path.name}"
        strategy.last_update = now_ms()
        strategy.updated_at = now_ms()

    file_record = db.session.get(File, file_id)
    if file_record is None:
        file_record = File(
            id=file_id,
            owner_id=None,
            filename=package_path.name,
            content_type="application/zip",
            size=package_path.stat().st_size,
            path=package_path.as_posix(),
        )
        db.session.add(file_record)
    else:
        file_record.path = package_path.as_posix()
        file_record.size = package_path.stat().st_size

    existing_version = StrategyVersion.query.filter_by(strategy_id=strategy_id, version=version).first()
    if existing_version is None:
        db.session.add(
            StrategyVersion(
                id=f"onboarding-version-{uuid.uuid4().hex[:8]}",
                strategy_id=strategy_id,
                version=version,
                file_id=file_record.id,
                checksum="onboarding-gold-step",
            )
        )

    db.session.commit()
    _onboarding_seeded = True


def _marketplace_visibility_clause():
    return and_(Strategy.is_public.is_(True), Strategy.review_status == "approved")
