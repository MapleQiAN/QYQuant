import uuid
from pathlib import Path

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from sqlalchemy import and_

from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus, File, Strategy, StrategyVersion, User
from ..schemas import StrategySchema
from ..utils.response import error_response, ok
from ..utils.storage import read_json
from ..utils.time import format_beijing_iso_ms, now_ms

bp = Blueprint("marketplace", __name__, url_prefix="/api/v1/marketplace")


@bp.get("/strategies")
def list_marketplace_strategies():
    featured = _bool_arg("featured", default=False)
    tag = (request.args.get("tag") or "").strip().lower()
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

    query = base_query.order_by(Strategy.last_update.desc(), Strategy.created_at.desc(), Strategy.id.desc())
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
    strategy = _get_public_strategy(strategy_id)
    if strategy is None:
        return error_response("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    imported_strategy = _find_imported_strategy(user_id, strategy)
    payload = {
        "id": strategy.id,
        "title": strategy.title or strategy.name,
        "description": strategy.description,
        "category": strategy.category,
        "tags": strategy.tags or [],
        "display_metrics": strategy.display_metrics or {},
        "is_verified": bool(strategy.is_verified),
        "created_at": format_beijing_iso_ms(strategy.created_at),
        "author": _serialize_author(strategy.owner_id),
        "already_imported": imported_strategy is not None,
        "imported_strategy_id": imported_strategy.id if imported_strategy else None,
        "has_equity_curve": _find_latest_completed_job(strategy.id) is not None,
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


def _get_public_strategy(strategy_id):
    return (
        Strategy.query
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


def _serialize_author(user_id):
    if not user_id:
        return {"nickname": "QYQuant", "avatar_url": ""}

    user = db.session.get(User, user_id)
    if user is None:
        return {"nickname": "QYQuant", "avatar_url": ""}
    return {
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
    }


def _find_imported_strategy(user_id, marketplace_strategy):
    if not user_id or not marketplace_strategy.code_hash:
        return None

    return (
        Strategy.query
        .filter(
            Strategy.owner_id == user_id,
            Strategy.code_hash == marketplace_strategy.code_hash,
            Strategy.id != marketplace_strategy.id,
        )
        .order_by(Strategy.created_at.desc())
        .first()
    )


def _onboarding_package_path():
    return Path(__file__).resolve().parents[2] / "strategy_store" / "GoldStepByStep.qys"


def _ensure_onboarding_strategy():
    existing = Strategy.query.filter(Strategy.owner_id.is_(None), _marketplace_visibility_clause()).all()
    if any(any(str(tag).strip().lower() == "onboarding" for tag in (item.tags or [])) for item in existing):
        return

    package_path = _onboarding_package_path()
    if not package_path.exists():
        return

    strategy_id = "onboarding-gold-step"
    file_id = "onboarding-gold-step-file"
    version = "0.1.0"

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


def _marketplace_visibility_clause():
    return and_(Strategy.is_public.is_(True), Strategy.review_status == "approved")
