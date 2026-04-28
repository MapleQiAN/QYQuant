import copy
import json
from pathlib import Path

import pytest

from app.qsga.verifiers.schema_verifier import verify_qyir_schema


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_trend_following_qyir_passes_schema_verifier():
    result = verify_qyir_schema(load_fixture("trend_following_basic.json"))

    assert result.passed
    assert result.to_dict() == {"status": "pass", "errors": []}


def test_valid_momentum_qyir_passes_schema_verifier():
    result = verify_qyir_schema(load_fixture("momentum_basic.json"))

    assert result.passed


def test_schema_verifier_reports_structured_errors_for_invalid_qyir():
    qyir = load_fixture("trend_following_basic.json")
    broken = copy.deepcopy(qyir)
    broken["strategy"]["family"] = "unknown_family"
    broken["signals"][0]["right"] = "missing_signal"
    broken["risk"]["max_position_pct"] = 120
    broken["universe"]["symbols"] = []

    result = verify_qyir_schema(broken)
    payload = result.to_dict()
    codes = {error["code"] for error in payload["errors"]}

    assert not result.passed
    assert "UNSUPPORTED_STRATEGY_FAMILY" in codes
    assert "UNKNOWN_SIGNAL_REFERENCE" in codes
    assert "INVALID_PERCENT" in codes
    assert "SYMBOLS_REQUIRED" in codes
    assert all({"code", "path", "message", "severity"} <= set(error) for error in payload["errors"])


def test_schema_verifier_rejects_unsupported_indicator_for_family():
    qyir = load_fixture("trend_following_basic.json")
    qyir["signals"][0]["indicator"] = "ema"

    result = verify_qyir_schema(qyir)

    assert not result.passed
    assert result.errors[0].code == "UNSUPPORTED_INDICATOR"


@pytest.mark.parametrize("case", load_fixture("invalid_cases.json"))
def test_invalid_qyir_fixtures_report_expected_error_codes(case):
    qyir = load_fixture("trend_following_basic.json")
    for path in case.get("remove", []):
        _remove_path(qyir, path)
    for path, value in (case.get("set") or {}).items():
        _set_path(qyir, path, value)

    result = verify_qyir_schema(qyir)
    codes = {error.code for error in result.errors}

    assert not result.passed
    assert case["expected_code"] in codes


def _set_path(target, dotted_path, value):
    current = target
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if part.isdigit() else current[part]
    last = parts[-1]
    if last.isdigit():
        current[int(last)] = value
    else:
        current[last] = value


def _remove_path(target, dotted_path):
    current = target
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if part.isdigit() else current[part]
    current.pop(parts[-1], None)
