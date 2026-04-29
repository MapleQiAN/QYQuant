from __future__ import annotations

from .backtest_verifier import extract_data_range, extract_summary
from ..errors import verification_error
from ..result import VerificationResult, fail_result, pass_result


HISTORICAL_SCOPE = "historical_backtest"


def audit_risk_constraints(qyir: dict, backtest_result: dict) -> dict:
    risk = qyir.get("risk") or {}
    execution = qyir.get("execution") or {}
    summary = extract_summary(backtest_result)
    data_range = extract_data_range(backtest_result)

    checks = [
        _max_drawdown_check(risk, summary, data_range),
        _max_position_check(risk, summary, backtest_result, data_range),
        _turnover_check(execution, backtest_result, data_range),
    ]
    checks = [check for check in checks if check is not None]
    status = "pass" if all(check["status"] in {"pass", "not_run"} for check in checks) else "violation"
    return {
        "status": status,
        "scope": HISTORICAL_SCOPE,
        "data_range": data_range,
        "checks": checks,
    }


def verify_risk_audit(audit: dict) -> VerificationResult:
    violations = [check for check in audit.get("checks", []) if check.get("status") == "violation"]
    if not violations:
        return pass_result()
    return fail_result(
        [
            verification_error(
                "RISK_AUDIT_VIOLATION",
                "$.risk",
                "历史回测风险约束未通过",
                category="risk",
                repairable=any(bool(item.get("repairable")) for item in violations),
            )
        ]
    )


def _max_drawdown_check(risk: dict, summary: dict, data_range: dict) -> dict | None:
    target = risk.get("max_drawdown_pct")
    observed = summary.get("maxDrawdown")
    if target is None:
        return None
    if observed is None:
        return _not_run("max_drawdown", target, data_range, ["add_stop_loss", "reduce_position_weight"])
    observed_value = float(observed)
    target_value = float(target)
    return _check(
        "max_drawdown",
        target_value,
        observed_value,
        "violation" if observed_value < -abs(target_value) else "pass",
        data_range,
        ["add_stop_loss", "reduce_position_weight"],
    )


def _max_position_check(risk: dict, summary: dict, backtest_result: dict, data_range: dict) -> dict | None:
    target = risk.get("max_position_pct")
    observed = summary.get("maxPositionPct")
    runtime = backtest_result.get("runtime") if isinstance(backtest_result.get("runtime"), dict) else {}
    if observed is None:
        observed = runtime.get("maxPositionPct")
    if target is None:
        return None
    if observed is None:
        return _not_run("max_position_pct", target, data_range, ["reduce_position_weight"])
    observed_value = float(observed)
    target_value = float(target)
    return _check(
        "max_position_pct",
        target_value,
        observed_value,
        "violation" if observed_value > target_value else "pass",
        data_range,
        ["reduce_position_weight"],
    )


def _turnover_check(execution: dict, backtest_result: dict, data_range: dict) -> dict | None:
    target = execution.get("max_orders_per_day")
    if target is None:
        return None
    observed = _observed_orders_per_day(backtest_result, data_range)
    if observed is None:
        return _not_run("turnover_orders_per_day", target, data_range, ["lower_rebalance_frequency"])
    target_value = float(target)
    return _check(
        "turnover_orders_per_day",
        target_value,
        observed,
        "violation" if observed > target_value else "pass",
        data_range,
        ["lower_rebalance_frequency"],
    )


def _observed_orders_per_day(backtest_result: dict, data_range: dict) -> float | None:
    summary = extract_summary(backtest_result)
    if summary.get("turnoverOrdersPerDay") is not None:
        return float(summary["turnoverOrdersPerDay"])
    trades = backtest_result.get("trades") or []
    start = data_range.get("start")
    end = data_range.get("end")
    if start is None or end is None:
        return None
    try:
        days = max((float(end) - float(start)) / 86_400_000, 1.0)
    except (TypeError, ValueError):
        return None
    return len(trades) / days


def _check(constraint: str, target: float, observed: float, status: str, data_range: dict, actions: list[str]) -> dict:
    return {
        "constraint": constraint,
        "target": target,
        "observed": observed,
        "status": status,
        "scope": HISTORICAL_SCOPE,
        "data_range": data_range,
        "repairable": status == "violation",
        "recommended_actions": actions if status == "violation" else [],
    }


def _not_run(constraint: str, target, data_range: dict, actions: list[str]) -> dict:
    return {
        "constraint": constraint,
        "target": target,
        "observed": None,
        "status": "not_run",
        "scope": HISTORICAL_SCOPE,
        "data_range": data_range,
        "repairable": False,
        "recommended_actions": actions,
    }
