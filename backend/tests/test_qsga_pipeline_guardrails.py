import json
from pathlib import Path

from app.extensions import db
from app.models import StrategyImportDraft
from app.qsga.pipeline import build_qsga_draft
from app.qsga.result import fail_result
from app.qsga.errors import verification_error


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_pipeline_rejected_intent_does_not_create_draft_or_compile(app, seed_user, monkeypatch):
    def fail_compile(*args, **kwargs):
        raise AssertionError("compiler must not run")

    monkeypatch.setattr("app.qsga.pipeline.compile_qyir_to_qysp_project", fail_compile)
    qyir = load_fixture("trend_following_basic.json")
    qyir["intent"]["raw_text"] = "保证收益，稳赚不亏"

    with app.app_context():
        before = StrategyImportDraft.query.count()
        result = build_qsga_draft(qyir, owner_id=seed_user.id)
        after = StrategyImportDraft.query.count()

    assert result["status"] == "rejected"
    assert result["verification"]["guardrails"]["errors"][0]["code"] == "UNSAFE_INTENT"
    assert before == after


def test_pipeline_clarification_intent_does_not_create_draft(app, seed_user, monkeypatch):
    def fail_compile(*args, **kwargs):
        raise AssertionError("compiler must not run")

    monkeypatch.setattr("app.qsga.pipeline.compile_qyir_to_qysp_project", fail_compile)
    qyir = load_fixture("trend_following_basic.json")
    qyir["intent"]["raw_text"] = "做一个低风险策略，稳一点"
    qyir["risk"].pop("max_drawdown_pct", None)
    qyir["risk"].pop("max_position_pct", None)

    with app.app_context():
        before = StrategyImportDraft.query.count()
        result = build_qsga_draft(qyir, owner_id=seed_user.id)
        after = StrategyImportDraft.query.count()

    assert result["status"] == "clarification_required"
    assert result["verification"]["guardrails"]["questions"]
    assert before == after


def test_pipeline_blocks_qysp_validation_failure(app, seed_user, monkeypatch):
    qyir = load_fixture("trend_following_basic.json")

    monkeypatch.setattr(
        "app.qsga.pipeline.verify_qysp_project",
        lambda _project_dir: fail_result(
            [
                verification_error(
                    "QYSP_VALIDATION_FAILED",
                    "$.qysp",
                    "invalid",
                    category="qysp",
                )
            ]
        ),
    )

    with app.app_context():
        result = build_qsga_draft(qyir, owner_id=seed_user.id)

    assert result["status"] == "blocked"
    assert result["verification"]["qysp"]["errors"][0]["code"] == "QYSP_VALIDATION_FAILED"


def test_pipeline_supported_fixture_still_creates_draft(app, seed_user):
    with app.app_context():
        result = build_qsga_draft(load_fixture("momentum_basic.json"), owner_id=seed_user.id)

        draft = db.session.get(StrategyImportDraft, result["analysis"]["draftImportId"])

    assert result["status"] == "draft_ready"
    assert result["verification"]["guardrails"]["status"] == "pass"
    assert result["verification"]["schema"]["status"] == "pass"
    assert result["verification"]["domain"]["status"] == "pass"
    assert result["verification"]["semantic"]["status"] == "pass"
    assert result["verification"]["qysp"]["status"] == "pass"
    assert result["verification"]["runtime"]["status"] == "pass"
    assert draft is not None
