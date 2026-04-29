import json
from pathlib import Path

from app.qsga.verifiers.risk_auditor import audit_risk_constraints, verify_risk_audit


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def backtest_result(summary=None, trades=None):
    return {
        "summary": summary or {"maxDrawdown": -8.0, "maxPositionPct": 25, "turnoverOrdersPerDay": 1},
        "kline": [{"time": 0, "close": 100}, {"time": 86_400_000, "close": 110}],
        "trades": trades or [],
        "dataSource": "mock",
    }


def test_risk_auditor_passes_historical_constraints():
    audit = audit_risk_constraints(load_fixture("trend_following_basic.json"), backtest_result())

    assert audit["status"] == "pass"
    assert audit["scope"] == "historical_backtest"
    assert verify_risk_audit(audit).passed


def test_risk_auditor_reports_repairable_drawdown_violation():
    audit = audit_risk_constraints(
        load_fixture("trend_following_basic.json"),
        backtest_result({"maxDrawdown": -20.0, "maxPositionPct": 25, "turnoverOrdersPerDay": 1}),
    )

    assert audit["status"] == "violation"
    drawdown = next(check for check in audit["checks"] if check["constraint"] == "max_drawdown")
    assert drawdown["observed"] == -20.0
    assert "reduce_position_weight" in drawdown["recommended_actions"]
    result = verify_risk_audit(audit)
    assert not result.passed
    assert result.errors[0].code == "RISK_AUDIT_VIOLATION"


def test_risk_auditor_checks_turnover_from_trades_when_summary_missing():
    audit = audit_risk_constraints(
        load_fixture("trend_following_basic.json"),
        backtest_result(
            {"maxDrawdown": -8.0, "maxPositionPct": 25},
            trades=[{"side": "buy"}, {"side": "sell"}, {"side": "buy"}],
        ),
    )

    turnover = next(check for check in audit["checks"] if check["constraint"] == "turnover_orders_per_day")
    assert turnover["status"] == "violation"
    assert turnover["observed"] == 3.0
