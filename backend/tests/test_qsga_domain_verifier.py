import json
from pathlib import Path

from app.qsga.verifiers.domain_verifier import verify_qyir_domain


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def codes(result):
    return {error.code for error in result.errors}


def test_domain_verifier_rejects_strategy_signal_mismatch():
    qyir = load_fixture("trend_following_basic.json")
    qyir["signals"] = [{"name": "fast_ma", "indicator": "ma", "window": 10, "operator": "gt"}]

    result = verify_qyir_domain(qyir)

    assert "DOMAIN_STRATEGY_SIGNAL_MISMATCH" in codes(result)


def test_domain_verifier_rejects_novice_high_position():
    qyir = load_fixture("trend_following_basic.json")
    qyir["risk"]["max_position_pct"] = 60

    result = verify_qyir_domain(qyir)

    assert "DOMAIN_RISK_TOO_AGGRESSIVE" in codes(result)


def test_domain_verifier_rejects_market_symbol_mismatch():
    qyir = load_fixture("trend_following_basic.json")
    qyir["universe"]["market"] = "crypto"
    qyir["universe"]["symbols"] = ["XAUUSD"]

    result = verify_qyir_domain(qyir)

    assert "DOMAIN_MARKET_SYMBOL_MISMATCH" in codes(result)


def test_domain_verifier_rejects_rebalance_order_conflict():
    qyir = load_fixture("momentum_basic.json")
    qyir["execution"]["rebalance"] = "monthly"
    qyir["execution"]["max_orders_per_day"] = 10

    result = verify_qyir_domain(qyir)

    assert "DOMAIN_REBALANCE_ORDER_CONFLICT" in codes(result)


def test_domain_verifier_passes_supported_fixtures():
    assert verify_qyir_domain(load_fixture("trend_following_basic.json")).passed
    assert verify_qyir_domain(load_fixture("momentum_basic.json")).passed
