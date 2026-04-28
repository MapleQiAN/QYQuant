import json
from pathlib import Path

from app.qsga.verifiers.semantic_verifier import verify_semantic_slots


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def codes(result):
    return {error.code for error in result.errors}


def test_semantic_verifier_rejects_position_constraint_weakening():
    qyir = load_fixture("trend_following_basic.json")
    qyir["risk"]["max_position_pct"] = 50

    result = verify_semantic_slots(qyir)

    assert "SEMANTIC_POSITION_WEAKENED" in codes(result)


def test_semantic_verifier_rejects_monthly_rebalance_weakening():
    qyir = load_fixture("momentum_basic.json")
    qyir["intent"]["raw_text"] = "做一个 BTC 动量策略，不要频繁交易，每月调仓"
    qyir["execution"]["rebalance"] = "daily"

    result = verify_semantic_slots(qyir)

    assert "SEMANTIC_REBALANCE_WEAKENED" in codes(result)


def test_semantic_verifier_rejects_drawdown_constraint_weakening():
    qyir = load_fixture("momentum_basic.json")
    qyir["intent"]["raw_text"] = "做一个 BTC 动量策略，最大回撤 10%"
    qyir["risk"]["max_drawdown_pct"] = 20

    result = verify_semantic_slots(qyir)

    assert "SEMANTIC_DRAWDOWN_WEAKENED" in codes(result)


def test_semantic_verifier_passes_supported_fixtures():
    assert verify_semantic_slots(load_fixture("trend_following_basic.json")).passed
    assert verify_semantic_slots(load_fixture("momentum_basic.json")).passed
