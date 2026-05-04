import json
from pathlib import Path

from app.extensions import db
from app.models import BacktestJob, BacktestJobStatus
from app.qsga.pipeline import build_qsga_draft


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def backtest_result(max_drawdown=-8.0, max_position=25.0, turnover=1.0):
    return {
        "summary": {
            "maxDrawdown": max_drawdown,
            "maxPositionPct": max_position,
            "turnoverOrdersPerDay": turnover,
        },
        "kline": [{"time": 0, "close": 100}, {"time": 86_400_000, "close": 110}],
        "trades": [],
        "dataSource": "mock",
    }


def test_pipeline_run_backtest_queues_async_verification(app, seed_user):
    qyir = load_fixture("trend_following_basic.json")

    with app.app_context():
        result = build_qsga_draft(
            qyir, owner_id=seed_user.id, options={"runBacktest": True}
        )
        job = db.session.get(BacktestJob, result["analysis"]["backtestJobId"])

    assert result["status"] == "running"
    assert result["verification"]["backtest"]["status"] == "running"
    assert result["trust"]["trusted"] is False
    assert result["analysis"]["qsgaTrust"]["runningChecks"] == ["backtest"]
    assert "risk" in result["analysis"]["qsgaTrust"]["missingChecks"]
    assert job is not None
    assert job.status == BacktestJobStatus.PENDING.value
    assert job.params["qsga"] is True
    assert job.params["draft_import_id"] == result["analysis"]["draftImportId"]


def test_pipeline_audits_supplied_backtest_result(app, seed_user):
    with app.app_context():
        result = build_qsga_draft(
            load_fixture("trend_following_basic.json"),
            owner_id=seed_user.id,
            options={"runBacktest": True, "backtestResult": backtest_result()},
        )

    assert result["status"] == "draft_ready"
    assert result["verification"]["backtest"]["status"] == "pass"
    assert result["verification"]["risk"]["status"] == "pass"
    assert result["trust"]["trusted"] is True
    assert result["analysis"]["isVerified"] is True
    assert result["analysis"]["riskAudit"]["scope"] == "historical_backtest"
    assert "未来" in result["analysis"]["historicalRiskNotice"]


def test_pipeline_blocks_risk_violation_without_repair_runner(app, seed_user):
    with app.app_context():
        result = build_qsga_draft(
            load_fixture("trend_following_basic.json"),
            owner_id=seed_user.id,
            options={
                "runBacktest": True,
                "backtestResult": backtest_result(max_drawdown=-20.0),
            },
        )

    assert result["status"] == "blocked"
    assert result["trust"]["trusted"] is False
    assert "risk" in result["trust"]["failedChecks"]
    assert result["verification"]["risk"]["errors"][0]["code"] == "RISK_AUDIT_VIOLATION"


def test_pipeline_repairs_then_recompiles_and_reaudits(app, seed_user):
    def runner(candidate, _draft_payload):
        if candidate["risk"]["max_position_pct"] < 30:
            return backtest_result(
                max_drawdown=-8.0, max_position=candidate["risk"]["max_position_pct"]
            )
        return backtest_result(
            max_drawdown=-20.0, max_position=candidate["risk"]["max_position_pct"]
        )

    with app.app_context():
        result = build_qsga_draft(
            load_fixture("trend_following_basic.json"),
            owner_id=seed_user.id,
            options={"runBacktest": True, "enableRepair": True, "maxRepairAttempts": 2},
            backtest_runner=runner,
        )

    assert result["status"] == "draft_ready"
    assert result["verification"]["risk"]["status"] == "pass"
    assert result["analysis"]["repairedQyir"]["risk"]["max_position_pct"] == 21.0
    assert result["analysis"]["repairHistory"][-1]["status"] == "passed"
