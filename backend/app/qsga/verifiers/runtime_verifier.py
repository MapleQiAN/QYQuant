from __future__ import annotations

from ..errors import verification_error
from ..result import VerificationResult, fail_result, pass_result


def verify_runtime_contract(qyir: dict, analysis: dict | None = None) -> VerificationResult:
    risk = qyir.get("risk") or {}
    candidates = (analysis or {}).get("entrypointCandidates") or []
    if analysis is not None and not any(candidate.get("callable") == "on_bar" for candidate in candidates):
        return fail_result(
            [
                verification_error(
                    "RUNTIME_ENTRYPOINT_MISSING",
                    "$.analysis.entrypointCandidates",
                    "runtime 预检需要 on_bar entrypoint",
                    category="runtime",
                )
            ]
        )
    if risk.get("max_position_pct") is None:
        return fail_result(
            [
                verification_error(
                    "RUNTIME_RISK_PARAMETER_MISSING",
                    "$.risk.max_position_pct",
                    "runtime 预检需要最大仓位参数",
                    category="runtime",
                )
            ]
        )
    return pass_result()
