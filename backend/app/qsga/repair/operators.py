from __future__ import annotations

from copy import deepcopy


def apply_repair_operator(qyir: dict, risk_audit: dict, operator: str) -> tuple[dict, dict]:
    candidate = deepcopy(qyir)
    checks = risk_audit.get("checks") or []
    if operator == "add_stop_loss":
        changed = _add_stop_loss(candidate, checks)
    elif operator == "reduce_position_weight":
        changed = _reduce_position_weight(candidate, checks)
    elif operator == "lower_rebalance_frequency":
        changed = _lower_rebalance_frequency(candidate, checks)
    else:
        changed = False

    return candidate, {
        "operator": operator,
        "status": "patched" if changed else "not_applicable",
        "trigger": _trigger_summary(checks, operator),
        "precondition": _precondition(operator),
        "postcondition": "recompile_verify_backtest_risk_audit",
    }


def recommended_operators(risk_audit: dict) -> list[str]:
    ordered = ["add_stop_loss", "reduce_position_weight", "lower_rebalance_frequency"]
    actions = {
        action
        for check in risk_audit.get("checks", [])
        if check.get("status") == "violation"
        for action in check.get("recommended_actions", [])
    }
    return [operator for operator in ordered if operator in actions]


def _add_stop_loss(qyir: dict, checks: list[dict]) -> bool:
    drawdown = _check(checks, "max_drawdown")
    if not drawdown:
        return False
    risk = qyir.setdefault("risk", {})
    target = abs(float(drawdown.get("target") or 10))
    proposed = max(1.0, round(target * 0.5, 2))
    current = risk.get("stop_loss_pct")
    if current is not None and float(current) <= proposed:
        return False
    risk["stop_loss_pct"] = proposed
    return True


def _reduce_position_weight(qyir: dict, checks: list[dict]) -> bool:
    risk = qyir.setdefault("risk", {})
    current = risk.get("max_position_pct")
    if current is None:
        return False
    position_check = _check(checks, "max_position_pct")
    if position_check:
        proposed = min(float(position_check.get("target") or current), float(current))
    else:
        proposed = float(current) * 0.7
    proposed = max(1.0, round(proposed, 2))
    if proposed >= float(current):
        return False
    risk["max_position_pct"] = proposed
    return True


def _lower_rebalance_frequency(qyir: dict, checks: list[dict]) -> bool:
    if not _check(checks, "turnover_orders_per_day"):
        return False
    execution = qyir.setdefault("execution", {})
    changed = False
    if execution.get("rebalance") != "monthly":
        execution["rebalance"] = "monthly"
        changed = True
    if execution.get("max_orders_per_day") != 1:
        execution["max_orders_per_day"] = 1
        changed = True
    return changed


def _check(checks: list[dict], constraint: str) -> dict | None:
    for check in checks:
        if check.get("constraint") == constraint and check.get("status") == "violation":
            return check
    return None


def _trigger_summary(checks: list[dict], operator: str) -> list[str]:
    return [
        f"{check.get('constraint')}:{check.get('observed')}:{check.get('target')}"
        for check in checks
        if operator in check.get("recommended_actions", []) and check.get("status") == "violation"
    ]


def _precondition(operator: str) -> str:
    return {
        "add_stop_loss": "risk.max_drawdown violation and stop_loss can be tightened",
        "reduce_position_weight": "drawdown or position violation and max_position can be reduced",
        "lower_rebalance_frequency": "turnover violation and execution cadence can be lowered",
    }.get(operator, "unknown")
