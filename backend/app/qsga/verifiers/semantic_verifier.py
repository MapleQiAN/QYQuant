from __future__ import annotations

import re

from ..errors import verification_error
from ..result import VerificationError, VerificationResult, fail_result, pass_result


_POSITION_RE = re.compile(r"仓位(?:不超过|不要超过|最高|小于|低于)\s*(\d+(?:\.\d+)?)\s*%")
_DRAWDOWN_RE = re.compile(r"(?:最大)?回撤(?:不超过|不要超过|小于|低于)?\s*(\d+(?:\.\d+)?)\s*%")
_STOP_LOSS_RE = re.compile(r"止损(?:不超过|不要超过|设置为|小于|低于)?\s*(\d+(?:\.\d+)?)\s*%")


def verify_semantic_slots(qyir: dict, expected_slots: dict | None = None) -> VerificationResult:
    expected = dict(expected_slots or {})
    expected.update(_extract_expected_slots(str((qyir.get("intent") or {}).get("raw_text") or "")))
    errors: list[VerificationError] = []
    risk = qyir.get("risk") or {}
    execution = qyir.get("execution") or {}
    strategy = qyir.get("strategy") or {}

    _check_max_value(
        errors,
        expected,
        "risk.max_position_pct",
        risk.get("max_position_pct"),
        "$.risk.max_position_pct",
        "SEMANTIC_POSITION_WEAKENED",
    )
    _check_max_value(
        errors,
        expected,
        "risk.max_drawdown_pct",
        risk.get("max_drawdown_pct"),
        "$.risk.max_drawdown_pct",
        "SEMANTIC_DRAWDOWN_WEAKENED",
    )
    _check_max_value(
        errors,
        expected,
        "risk.stop_loss_pct",
        risk.get("stop_loss_pct"),
        "$.risk.stop_loss_pct",
        "SEMANTIC_STOP_LOSS_WEAKENED",
    )

    if expected.get("execution.rebalance") == "monthly" and execution.get("rebalance") != "monthly":
        errors.append(
            verification_error(
                "SEMANTIC_REBALANCE_WEAKENED",
                "$.execution.rebalance",
                "用户要求月度或更低频调仓，QYIR 不得提升交易频率",
                category="semantic",
            )
        )

    if expected.get("risk.low_risk") is True:
        max_position = risk.get("max_position_pct")
        if strategy.get("direction") not in {"long_only", "flat_or_long"} or not isinstance(max_position, (int, float)) or max_position > 50:
            errors.append(
                verification_error(
                    "SEMANTIC_LOW_RISK_WEAKENED",
                    "$.risk.max_position_pct",
                    "用户要求低风险或不加杠杆，QYIR 不得使用高仓位或高风险方向",
                    category="semantic",
                )
            )

    return fail_result(errors) if errors else pass_result()


def _extract_expected_slots(text: str) -> dict:
    expected: dict[str, object] = {}
    _extract_percent(text, _POSITION_RE, expected, "risk.max_position_pct")
    _extract_percent(text, _DRAWDOWN_RE, expected, "risk.max_drawdown_pct")
    _extract_percent(text, _STOP_LOSS_RE, expected, "risk.stop_loss_pct")
    if "月度" in text or "每月" in text or "不要频繁交易" in text:
        expected["execution.rebalance"] = "monthly"
    if "不加杠杆" in text or "低风险" in text:
        expected["risk.low_risk"] = True
    return expected


def _extract_percent(text: str, pattern: re.Pattern, expected: dict, key: str) -> None:
    match = pattern.search(text)
    if match:
        expected[key] = float(match.group(1))


def _check_max_value(
    errors: list[VerificationError],
    expected: dict,
    key: str,
    actual: object,
    path: str,
    code: str,
) -> None:
    target = expected.get(key)
    if target is None:
        return
    if not isinstance(actual, (int, float)) or actual > float(target):
        errors.append(
            verification_error(
                code,
                path,
                "QYIR 弱化了用户明确给出的约束槽位",
                category="semantic",
                repairable=True,
            )
        )
