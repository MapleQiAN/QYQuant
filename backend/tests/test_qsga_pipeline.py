import json
from pathlib import Path

from app.extensions import db
from app.models import StrategyImportDraft
from app.qsga.pipeline import build_qsga_draft


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_build_qsga_draft_creates_strategy_import_draft(app, seed_user):
    with app.app_context():
        result = build_qsga_draft(load_fixture("trend_following_basic.json"), owner_id=seed_user.id)

        draft_id = result["analysis"]["draftImportId"]
        draft = db.session.get(StrategyImportDraft, draft_id)

        assert result["status"] == "draft_ready"
        assert result["verification"]["schema"]["status"] == "pass"
        assert result["verification"]["qysp"]["status"] == "pass"
        assert draft is not None
        assert draft.owner_id == seed_user.id
        assert draft.source_type == "qys_package"
        assert draft.analysis_payload["entrypointCandidates"][0]["callable"] == "on_bar"
