import logging
import os
from pathlib import Path

from celery.utils.log import get_task_logger
from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import Strategy, StrategyReview
from ..services.notifications import create_notification
from ..services.strategy_review import run_base_review, run_ai_enhancement
from ..utils.time import now_utc

logger = get_task_logger(__name__) if logging.getLogger().handlers else logging.getLogger(__name__)


def _get_strategy_code(strategy):
    if not strategy.storage_key:
        return None

    storage_root = Path(
        os.getenv("STRATEGY_STORAGE_DIR")
        or Path(__file__).resolve().parents[2] / "storage"
    )
    code_path = storage_root / strategy.storage_key / "strategy.py"
    if not code_path.exists():
        return None

    return code_path.read_text(encoding="utf-8")


def _run_review(strategy_id):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        logger.error("Review task: strategy %s not found", strategy_id)
        return {"status": "missing"}

    if strategy.review_status != "pending":
        logger.info("Review task: strategy %s is %s, skipping", strategy_id, strategy.review_status)
        return {"status": "skipped"}

    code = _get_strategy_code(strategy)

    base_result = run_base_review(
        code=code or "",
        display_metrics=strategy.display_metrics or {},
        metadata={
            "title": strategy.title or "",
            "description": strategy.description or "",
            "tags": strategy.tags or [],
            "category": strategy.category or "",
        },
    )

    ai_result = None
    ai_enabled = False
    if base_result["verdict"] == "approved":
        ai_result = run_ai_enhancement(
            code=code or "",
            metadata={
                "title": strategy.title or "",
                "description": strategy.description or "",
                "tags": strategy.tags or [],
                "category": strategy.category or "",
            },
            metrics=strategy.display_metrics or {},
        )
        if ai_result is not None:
            ai_enabled = True
            if ai_result.get("recommendation") == "reject" and ai_result.get("score", 100) < 40:
                base_result["verdict"] = "rejected"
                base_result["review_notes"] += f" | AI rejected (score: {ai_result['score']}/100)"

    verdict = base_result["verdict"]

    review = StrategyReview(
        strategy_id=strategy_id,
        status=verdict,
        code_safety=base_result["code_safety"],
        metrics_check=base_result["metrics_check"],
        metadata_check=base_result["metadata_check"],
        ai_analysis=ai_result,
        ai_enabled=ai_enabled,
        verdict=verdict,
        review_notes=base_result["review_notes"],
        reviewed_at=now_utc(),
    )
    db.session.add(review)

    strategy.review_status = verdict
    if verdict == "approved":
        strategy.is_public = True

    try:
        if strategy.owner_id:
            status_text = "approved" if verdict == "approved" else "rejected"
            create_notification(
                user_id=strategy.owner_id,
                type="strategy_review_result",
                title=f"Strategy {status_text}: {strategy.title or strategy.name}",
                content=base_result["review_notes"],
            )
    except Exception as exc:
        logger.error("Failed to send review notification: %s", exc)

    db.session.commit()

    return {"status": verdict, "review_id": review.id}


@celery_app.task(
    bind=True,
    name='app.tasks.review_tasks.review_strategy',
    soft_time_limit=int(os.getenv('REVIEW_TASK_SOFT_TIME_LIMIT', '120')),
    time_limit=int(os.getenv('REVIEW_TASK_TIME_LIMIT', '180')),
)
def review_strategy(self, strategy_id):
    if has_app_context():
        return _run_review(strategy_id)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _run_review(strategy_id)
