import uuid
from pathlib import Path

from flask import request
from flask_smorest import Blueprint

from ..extensions import db
from ..models import File, Strategy, StrategyVersion, User
from ..utils.response import ok
from ..utils.time import now_ms

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
            Strategy.query.filter(Strategy.owner_id.is_(None))
            .order_by(Strategy.last_update.desc(), Strategy.created_at.desc())
            .all()
        )
        items = [
            item
            for item in items
            if any(str(entry).strip().lower() == "onboarding" for entry in (item.tags or []))
        ]
        return ok(
            [item.to_card_dict(author=None) for item in items],
            meta={"total": len(items), "page": 1, "page_size": len(items)},
        )

    base_query = (
        db.session.query(Strategy, User)
        .join(User, Strategy.owner_id == User.id)
        .filter(Strategy.is_public.is_(True), Strategy.review_status == "approved")
    )

    if featured:
        query = (
            base_query.filter(Strategy.is_featured.is_(True))
            .order_by(Strategy.created_at.desc(), Strategy.id.desc())
        )
        total = query.count()
        items = query.limit(6).all()
        return ok(
            [strategy.to_card_dict(author=author) for strategy, author in items],
            meta={
                "total": total,
                "page": 1,
                "page_size": 6,
            },
        )

    query = base_query.order_by(Strategy.created_at.desc(), Strategy.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        [strategy.to_card_dict(author=author) for strategy, author in items],
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


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


def _onboarding_package_path():
    return Path(__file__).resolve().parents[2] / "strategy_store" / "GoldStepByStep.qys"


def _ensure_onboarding_strategy():
    existing = Strategy.query.filter(Strategy.owner_id.is_(None)).all()
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
            storage_key=f"strategy_store/{package_path.name}",
            last_update=now_ms(),
            updated_at=now_ms(),
            review_status="approved",
            is_public=False,
            is_featured=False,
            is_verified=False,
            display_metrics={},
        )
        db.session.add(strategy)
    else:
        strategy.tags = list({*(strategy.tags or []), "onboarding", "gold", "guided"})
        strategy.owner_id = None
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
