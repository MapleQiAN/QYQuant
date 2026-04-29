from __future__ import annotations

from ..errors import verification_error
from ..result import VerificationResult, fail_result, pass_result


def verify_backtest_result(backtest_result: dict | None) -> VerificationResult:
    if not isinstance(backtest_result, dict):
        return fail_result(
            [
                verification_error(
                    "BACKTEST_RESULT_MISSING",
                    "$.backtest",
                    "backtest verifier 需要回测结果",
                    category="backtest",
                )
            ]
        )

    summary = backtest_result.get("summary") or backtest_result.get("result_summary")
    if not isinstance(summary, dict):
        return fail_result(
            [
                verification_error(
                    "BACKTEST_SUMMARY_MISSING",
                    "$.backtest.summary",
                    "backtest verifier 需要 summary",
                    category="backtest",
                )
            ]
        )

    data_range = extract_data_range(backtest_result)
    if data_range.get("start") is None or data_range.get("end") is None:
        return fail_result(
            [
                verification_error(
                    "BACKTEST_DATA_RANGE_MISSING",
                    "$.backtest.data_range",
                    "风险审计必须记录历史数据范围",
                    category="backtest",
                )
            ]
        )
    return pass_result()


def extract_summary(backtest_result: dict) -> dict:
    return dict(backtest_result.get("summary") or backtest_result.get("result_summary") or {})


def extract_data_range(backtest_result: dict) -> dict:
    explicit = backtest_result.get("data_range") or backtest_result.get("dataRange")
    if isinstance(explicit, dict):
        return {"start": explicit.get("start"), "end": explicit.get("end"), "source": explicit.get("source")}

    bars = backtest_result.get("kline") or backtest_result.get("bars") or []
    if not bars:
        return {"start": None, "end": None, "source": backtest_result.get("dataSource")}
    return {
        "start": bars[0].get("time"),
        "end": bars[-1].get("time"),
        "source": backtest_result.get("dataSource"),
    }
