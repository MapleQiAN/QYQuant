import json
from pathlib import Path

from app.qsga.repair.loop import run_repair_loop
from app.qsga.verifiers.risk_auditor import audit_risk_constraints


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def make_result(max_drawdown, max_position):
    return {
        "summary": {"maxDrawdown": max_drawdown, "maxPositionPct": max_position, "turnoverOrdersPerDay": 1},
        "kline": [{"time": 0, "close": 100}, {"time": 86_400_000, "close": 110}],
        "trades": [],
    }


def test_repair_loop_reduces_position_and_requires_postcondition_pass():
    qyir = load_fixture("trend_following_basic.json")
    initial_audit = audit_risk_constraints(qyir, make_result(-20, 30))

    def build(candidate):
        return {"status": "draft_ready", "analysis": {"draftImportId": str(candidate["risk"]["max_position_pct"])}}

    def run(candidate, _draft):
        if candidate["risk"]["max_position_pct"] < 30:
            return make_result(-8, candidate["risk"]["max_position_pct"])
        return make_result(-20, candidate["risk"]["max_position_pct"])

    result = run_repair_loop(qyir, initial_audit, draft_builder=build, backtest_runner=run, max_attempts=2)

    assert result["status"] == "repaired"
    assert result["qyir"]["risk"]["max_position_pct"] == 21.0
    assert result["history"][-1]["status"] == "passed"


def test_repair_loop_blocks_after_attempt_budget():
    qyir = load_fixture("trend_following_basic.json")
    initial_audit = audit_risk_constraints(qyir, make_result(-20, 30))

    result = run_repair_loop(
        qyir,
        initial_audit,
        draft_builder=lambda _candidate: {"status": "draft_ready", "analysis": {}},
        backtest_runner=lambda candidate, _draft: make_result(-20, candidate["risk"]["max_position_pct"]),
        max_attempts=1,
    )

    assert result["status"] == "blocked"
    assert len(result["history"]) == 1
