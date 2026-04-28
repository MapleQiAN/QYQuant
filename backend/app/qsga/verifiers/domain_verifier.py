from __future__ import annotations

from ..compiler.template_registry import TEMPLATE_REGISTRY
from ..errors import verification_error
from ..result import VerificationError, VerificationResult, fail_result, pass_result


def verify_qyir_domain(qyir: dict) -> VerificationResult:
    errors: list[VerificationError] = []
    intent = qyir.get("intent") or {}
    strategy = qyir.get("strategy") or {}
    universe = qyir.get("universe") or {}
    risk = qyir.get("risk") or {}
    execution = qyir.get("execution") or {}
    signals = qyir.get("signals") or []

    if intent.get("classification") != "supported":
        errors.append(
            verification_error(
                "DOMAIN_INTENT_NOT_SUPPORTED",
                "$.intent.classification",
                "只有 supported QYIR 才能进入编译",
                category="domain",
            )
        )

    family = strategy.get("family")
    if family not in TEMPLATE_REGISTRY:
        errors.append(
            verification_error(
                "DOMAIN_TEMPLATE_NOT_FOUND",
                "$.strategy.family",
                "策略族没有可用 QYSP 模板",
                category="domain",
            )
        )
    elif not _family_signals_match(family, signals):
        errors.append(
            verification_error(
                "DOMAIN_STRATEGY_SIGNAL_MISMATCH",
                "$.signals",
                f"{family} 策略缺少可编译的信号组合",
                category="domain",
            )
        )

    raw_text = str(intent.get("raw_text") or "")
    audience = str((qyir.get("explanation") or {}).get("audience") or "")
    max_position = risk.get("max_position_pct")
    if ("新手" in raw_text or audience == "beginner") and isinstance(max_position, (int, float)) and max_position > 50:
        errors.append(
            verification_error(
                "DOMAIN_RISK_TOO_AGGRESSIVE",
                "$.risk.max_position_pct",
                "新手策略默认最大仓位不能高于 50%",
                category="domain",
                repairable=True,
            )
        )

    rebalance = execution.get("rebalance")
    max_orders = execution.get("max_orders_per_day")
    if isinstance(max_orders, int):
        if rebalance == "monthly" and max_orders > 2:
            errors.append(_rebalance_order_error())
        if rebalance in {"daily", "weekly"} and max_orders > 5:
            errors.append(_rebalance_order_error())

    market = universe.get("market")
    symbols = universe.get("symbols") or []
    for index, symbol in enumerate(symbols):
        if not _market_symbol_match(market, symbol):
            errors.append(
                verification_error(
                    "DOMAIN_MARKET_SYMBOL_MISMATCH",
                    f"$.universe.symbols[{index}]",
                    "市场与标的格式不匹配",
                    category="domain",
                )
            )

    return fail_result(errors) if errors else pass_result()


def _family_signals_match(family: str, signals: list) -> bool:
    if family == "trend_following":
        return any(_is_cross_signal(signal) for signal in signals) and any(_operator(signal) == "reference" for signal in signals)
    if family == "momentum":
        windows = [signal.get("window") for signal in signals if isinstance(signal, dict) and isinstance(signal.get("window"), int)]
        return len(windows) >= 2 and min(windows) < max(windows)
    return False


def _is_cross_signal(signal: object) -> bool:
    return isinstance(signal, dict) and _operator(signal) in {"cross_up", "cross_down"} and bool(signal.get("right"))


def _operator(signal: object) -> str | None:
    return signal.get("operator") if isinstance(signal, dict) else None


def _market_symbol_match(market: str | None, symbol: str) -> bool:
    if not isinstance(symbol, str) or not symbol.strip():
        return False
    normalized = symbol.upper()
    if market == "gold":
        return normalized == "XAUUSD"
    if market == "crypto":
        return normalized.endswith("USDT")
    return True


def _rebalance_order_error() -> VerificationError:
    return verification_error(
        "DOMAIN_REBALANCE_ORDER_CONFLICT",
        "$.execution.max_orders_per_day",
        "调仓频率与每日最大订单数设置矛盾",
        category="domain",
        repairable=True,
    )
