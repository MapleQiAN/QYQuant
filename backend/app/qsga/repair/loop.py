from __future__ import annotations

from collections.abc import Callable

from .operators import apply_repair_operator, recommended_operators
from ..verifiers.backtest_verifier import verify_backtest_result
from ..verifiers.risk_auditor import audit_risk_constraints, verify_risk_audit


BacktestRunner = Callable[[dict, dict], dict]
DraftBuilder = Callable[[dict], dict]


def run_repair_loop(
    qyir: dict,
    risk_audit: dict,
    *,
    draft_builder: DraftBuilder,
    backtest_runner: BacktestRunner,
    max_attempts: int = 2,
) -> dict:
    current = qyir
    history = []
    for operator in recommended_operators(risk_audit)[: max(0, max_attempts)]:
        candidate, entry = apply_repair_operator(current, risk_audit, operator)
        if entry["status"] != "patched":
            history.append(entry)
            continue

        draft_payload = draft_builder(candidate)
        backtest_result = backtest_runner(candidate, draft_payload)
        backtest_verification = verify_backtest_result(backtest_result)
        entry["backtest"] = backtest_verification.to_dict()
        if not backtest_verification.passed:
            entry["status"] = "failed"
            history.append(entry)
            current = candidate
            continue

        next_audit = audit_risk_constraints(candidate, backtest_result)
        risk_verification = verify_risk_audit(next_audit)
        entry["risk"] = risk_verification.to_dict()
        entry["audit"] = next_audit
        entry["draftImportId"] = draft_payload.get("analysis", {}).get("draftImportId")
        if risk_verification.passed:
            entry["status"] = "passed"
            history.append(entry)
            return {
                "status": "repaired",
                "qyir": candidate,
                "draft": draft_payload,
                "backtest_result": backtest_result,
                "risk_audit": next_audit,
                "history": history,
            }
        entry["status"] = "failed"
        history.append(entry)
        current = candidate
        risk_audit = next_audit

    return {
        "status": "blocked",
        "qyir": current,
        "history": history,
    }
