import copy
import json
from pathlib import Path

from app.qsga.guardrails import verify_intent_guardrails


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def with_text(text, *, classification="supported"):
    qyir = copy.deepcopy(load_fixture("trend_following_basic.json"))
    qyir["intent"]["raw_text"] = text
    qyir["intent"]["classification"] = classification
    return qyir


def test_guardrails_reject_unsafe_intent():
    result = verify_intent_guardrails(with_text("帮我做一个保证收益、稳赚不亏的策略"))

    assert result.status == "rejected"
    assert result.errors[0].code == "UNSAFE_INTENT"
    assert result.errors[0].category == "safety"


def test_guardrails_block_unsupported_intent():
    result = verify_intent_guardrails(with_text("做一个期权高频盘口自动实盘策略"))

    assert result.status == "blocked"
    assert result.errors[0].code == "UNSUPPORTED_INTENT"


def test_guardrails_request_clarification_for_ambiguous_intent_without_slots():
    qyir = with_text("做一个低风险策略，稳一点")
    qyir["risk"].pop("max_drawdown_pct", None)
    qyir["risk"].pop("max_position_pct", None)

    result = verify_intent_guardrails(qyir)

    assert result.status == "clarification_required"
    assert result.questions[0].path == "$.risk.max_drawdown_pct"


def test_guardrails_pass_supported_fixture():
    result = verify_intent_guardrails(load_fixture("trend_following_basic.json"))

    assert result.passed
