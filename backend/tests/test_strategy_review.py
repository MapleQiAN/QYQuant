import os
import pytest


class TestStrategyReviewModel:
    def test_create_basic_review(self, app):
        from app.extensions import db
        from app.models import StrategyReview

        with app.app_context():
            review = StrategyReview(
                strategy_id="test-strategy-id",
                status="pending",
            )
            db.session.add(review)
            db.session.commit()

            fetched = db.session.get(StrategyReview, review.id)
            assert fetched is not None
            assert fetched.status == "pending"
            assert fetched.code_safety is None
            assert fetched.ai_enabled is False

    def test_create_review_with_results(self, app):
        from app.extensions import db
        from app.models import StrategyReview

        with app.app_context():
            review = StrategyReview(
                strategy_id="test-strategy-id",
                status="approved",
                code_safety={"passed": True, "issues": []},
                metrics_check={"passed": True, "issues": []},
                metadata_check={"passed": True, "issues": []},
                ai_analysis={"score": 85, "risks": [], "summary": "Looks good"},
                ai_enabled=True,
                verdict="approved",
                review_notes="All checks passed. AI score: 85/100.",
            )
            db.session.add(review)
            db.session.commit()

            fetched = db.session.get(StrategyReview, review.id)
            assert fetched.verdict == "approved"
            assert fetched.ai_enabled is True
            assert fetched.ai_analysis["score"] == 85


class TestCodeSafetyScanner:
    def test_clean_code_passes(self):
        from app.services.strategy_review import scan_code_safety

        code = "def on_bar(context, bar): pass"
        result = scan_code_safety(code)
        assert result["passed"] is True
        assert result["issues"] == []

    def test_os_system_detected(self):
        from app.services.strategy_review import scan_code_safety

        code = "import os\nos.system('rm -rf /')"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any(i["severity"] == "critical" for i in result["issues"])

    def test_subprocess_detected(self):
        from app.services.strategy_review import scan_code_safety

        code = "import subprocess\nsubprocess.run(['ls'])"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("subprocess" in i["pattern"] for i in result["issues"])

    def test_eval_detected(self):
        from app.services.strategy_review import scan_code_safety

        code = "x = eval('1+1')"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("eval" in i["pattern"] for i in result["issues"])

    def test_exec_detected(self):
        from app.services.strategy_review import scan_code_safety

        code = "exec('print(1)')"
        result = scan_code_safety(code)
        assert result["passed"] is False

    def test_import_os_warning_only(self):
        from app.services.strategy_review import scan_code_safety

        code = "import os\npath = os.path.join('a', 'b')"
        result = scan_code_safety(code)
        criticals = [i for i in result["issues"] if i["severity"] == "critical"]
        assert len(criticals) == 0
        assert any(i["severity"] == "warning" for i in result["issues"])

    def test_network_import_detected(self):
        from app.services.strategy_review import scan_code_safety

        code = "import requests\nrequests.get('http://evil.com')"
        result = scan_code_safety(code)
        assert result["passed"] is False

    def test_syntax_error_code_handled(self):
        from app.services.strategy_review import scan_code_safety

        code = "def broken(:\n  pass"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("syntax_error" in i.get("type", "") for i in result["issues"])

    def test_empty_code_passes(self):
        from app.services.strategy_review import scan_code_safety

        code = ""
        result = scan_code_safety(code)
        assert result["passed"] is True


class TestMetricsCheck:
    def test_passing_metrics(self):
        from app.services.strategy_review import check_metrics

        result = check_metrics({
            "win_rate": 0.55,
            "returns": 0.12,
            "max_drawdown": 0.25,
        })
        assert result["passed"] is True
        assert result["issues"] == []

    def test_low_win_rate(self):
        from app.services.strategy_review import check_metrics

        result = check_metrics({"win_rate": 0.2, "returns": 0.1, "max_drawdown": 0.3})
        assert result["passed"] is False
        assert any("win_rate" in i["field"] for i in result["issues"])

    def test_high_drawdown(self):
        from app.services.strategy_review import check_metrics

        result = check_metrics({"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.95})
        assert result["passed"] is False
        assert any("max_drawdown" in i["field"] for i in result["issues"])

    def test_negative_returns(self):
        from app.services.strategy_review import check_metrics

        result = check_metrics({"win_rate": 0.5, "returns": -0.8, "max_drawdown": 0.3})
        assert result["passed"] is False

    def test_empty_metrics(self):
        from app.services.strategy_review import check_metrics

        result = check_metrics({})
        assert result["passed"] is False


class TestMetadataCheck:
    def test_complete_metadata(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": "My Alpha Strategy",
            "description": "This is a momentum-based strategy for A-shares.",
            "tags": ["momentum"],
            "category": "trend",
        })
        assert result["passed"] is True

    def test_short_title(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": "AB",
            "description": "A" * 30,
            "tags": ["x"],
            "category": "trend",
        })
        assert result["passed"] is False
        assert any("title" in i["field"] for i in result["issues"])

    def test_short_description(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": "Good Title",
            "description": "Too short",
            "tags": ["x"],
            "category": "trend",
        })
        assert result["passed"] is False

    def test_missing_tags(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": "Good Title",
            "description": "A" * 30,
            "tags": [],
            "category": "trend",
        })
        assert result["passed"] is False

    def test_missing_category(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": "Good Title",
            "description": "A" * 30,
            "tags": ["x"],
            "category": "",
        })
        assert result["passed"] is False

    def test_none_values(self):
        from app.services.strategy_review import check_metadata

        result = check_metadata({
            "title": None,
            "description": None,
            "tags": None,
            "category": None,
        })
        assert result["passed"] is False


class TestBaseReviewOrchestrator:
    def test_all_pass_approves(self, app):
        from app.services.strategy_review import run_base_review

        with app.app_context():
            result = run_base_review(
                code="def on_bar(ctx, bar): pass",
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                metadata={
                    "title": "Test Strategy",
                    "description": "A good strategy for testing purposes",
                    "tags": ["test"],
                    "category": "trend",
                },
            )
            assert result["verdict"] == "approved"
            assert result["code_safety"]["passed"] is True
            assert result["metrics_check"]["passed"] is True
            assert result["metadata_check"]["passed"] is True

    def test_code_dangerous_rejects(self, app):
        from app.services.strategy_review import run_base_review

        with app.app_context():
            result = run_base_review(
                code="import os\nos.system('rm -rf /')",
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                metadata={
                    "title": "Bad Code",
                    "description": "Dangerous strategy with malicious code",
                    "tags": ["bad"],
                    "category": "other",
                },
            )
            assert result["verdict"] == "rejected"
            assert result["code_safety"]["passed"] is False


class TestAIEnhancement:
    def test_ai_not_configured_skips(self, app):
        from app.services.strategy_review import run_ai_enhancement

        with app.app_context():
            monkeypatch = pytest.MonkeyPatch()
            monkeypatch.delenv("REVIEW_AI_PROVIDER", raising=False)
            monkeypatch.delenv("REVIEW_AI_API_KEY", raising=False)
            try:
                result = run_ai_enhancement(
                    code="def on_bar(ctx, bar): pass",
                    metadata={"title": "Test", "description": "A strategy", "category": "trend", "tags": ["x"]},
                    metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.2},
                )
                assert result is None
            finally:
                monkeypatch.undo()

    def test_ai_returns_analysis(self, app):
        from unittest.mock import patch
        from app.services.strategy_review import run_ai_enhancement

        with app.app_context():
            monkeypatch = pytest.MonkeyPatch()
            monkeypatch.setenv("REVIEW_AI_PROVIDER", "openai")
            monkeypatch.setenv("REVIEW_AI_API_KEY", "test-key")
            monkeypatch.setenv("REVIEW_AI_MODEL", "gpt-4o-mini")
            try:
                with patch("app.services.strategy_review._call_ai_provider") as mock_ai:
                    mock_ai.return_value = {
                        "score": 75,
                        "risks": ["No stop-loss detected"],
                        "summary": "Reasonable strategy with minor risks",
                        "recommendation": "approve",
                    }
                    result = run_ai_enhancement(
                        code="def on_bar(ctx, bar): pass",
                        metadata={"title": "Test", "description": "A strategy", "category": "trend", "tags": ["x"]},
                        metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.2},
                    )
                    assert result is not None
                    assert result["score"] == 75
                    assert result["recommendation"] == "approve"
            finally:
                monkeypatch.undo()


class TestReviewCeleryTask:
    def test_review_clean_strategy_approves(self, app):
        from app.extensions import db
        from app.models import Strategy, StrategyReview
        from app.tasks.review_tasks import review_strategy
        from pathlib import Path

        with app.app_context():
            strategy = Strategy(
                name="test-review-clean",
                symbol="000001",
                status="draft",
                source="editor",
                owner_id=None,
                title="Good Strategy",
                description="A well-tested momentum strategy for A-share market",
                category="trend",
                tags=["momentum"],
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                review_status="pending",
                returns=0.15,
                win_rate=0.6,
                max_drawdown=0.2,
                last_update=0,
                trades=100,
            )
            db.session.add(strategy)
            db.session.commit()
            strategy_id = strategy.id

            storage_root = Path(os.environ.get("STRATEGY_STORAGE_DIR", "/tmp"))
            code_dir = storage_root / f"editor/test-review/{strategy_id}"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "strategy.py").write_text("def on_bar(ctx, bar): pass")

            strategy.storage_key = f"editor/test-review/{strategy_id}"
            db.session.commit()

        result = review_strategy(strategy_id)
        assert result["status"] == "approved"

        with app.app_context():
            strategy = db.session.get(Strategy, strategy_id)
            assert strategy.review_status == "approved"
            assert strategy.is_public is True

            review_record = StrategyReview.query.filter_by(strategy_id=strategy_id).first()
            assert review_record is not None
            assert review_record.verdict == "approved"

    def test_review_dangerous_code_rejects(self, app):
        from app.extensions import db
        from app.models import Strategy, StrategyReview
        from app.tasks.review_tasks import review_strategy
        from pathlib import Path

        with app.app_context():
            strategy = Strategy(
                name="test-review-bad",
                symbol="000001",
                status="draft",
                source="editor",
                owner_id=None,
                title="Evil Strategy",
                description="A strategy with malicious code that should be rejected",
                category="other",
                tags=["bad"],
                display_metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.3},
                review_status="pending",
                returns=0.1,
                win_rate=0.5,
                max_drawdown=0.3,
                last_update=0,
                trades=50,
            )
            db.session.add(strategy)
            db.session.commit()
            strategy_id = strategy.id

            storage_root = Path(os.environ.get("STRATEGY_STORAGE_DIR", "/tmp"))
            code_dir = storage_root / f"editor/test-review/{strategy_id}"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "strategy.py").write_text("import os\nos.system('rm -rf /')")

            strategy.storage_key = f"editor/test-review/{strategy_id}"
            db.session.commit()

        result = review_strategy(strategy_id)
        assert result["status"] == "rejected"

        with app.app_context():
            strategy = db.session.get(Strategy, strategy_id)
            assert strategy.review_status == "rejected"

    def test_review_idempotent_skip(self, app):
        from app.tasks.review_tasks import review_strategy

        result = review_strategy("nonexistent-id")
        assert result["status"] == "missing"
