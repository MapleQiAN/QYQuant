from __future__ import annotations

from ..errors import verification_error
from ..result import VerificationError, VerificationResult, fail_result, pass_result
from ..schemas import (
    REQUIRED_TOP_LEVEL_FIELDS,
    SUPPORTED_CLASSIFICATIONS,
    SUPPORTED_DIRECTIONS,
    SUPPORTED_MARKETS,
    SUPPORTED_REBALANCE,
    SUPPORTED_TIMEFRAMES,
)
from ..compiler.template_registry import get_template_spec


def verify_qyir_schema(qyir: dict) -> VerificationResult:
    errors: list[VerificationError] = []

    if not isinstance(qyir, dict):
        return fail_result([_error("QYIR_TYPE", "$", "QYIR must be an object")])

    for field in sorted(REQUIRED_TOP_LEVEL_FIELDS - set(qyir.keys())):
        errors.append(_error("REQUIRED_FIELD_MISSING", f"$.{field}", f"Missing required field: {field}"))

    if errors:
        return fail_result(errors)

    if qyir.get("version") != "1.0":
        errors.append(_error("INVALID_VERSION", "$.version", "QYIR version must be 1.0"))

    intent = _object(qyir, "intent", errors)
    strategy = _object(qyir, "strategy", errors)
    universe = _object(qyir, "universe", errors)
    risk = _object(qyir, "risk", errors)
    execution = _object(qyir, "execution", errors)
    signals = qyir.get("signals")

    if intent is not None:
        _enum(intent, "classification", SUPPORTED_CLASSIFICATIONS, "$.intent.classification", errors)
        raw_text = intent.get("raw_text")
        if not isinstance(raw_text, str) or not raw_text.strip():
            errors.append(_error("RAW_TEXT_REQUIRED", "$.intent.raw_text", "intent.raw_text is required"))

    template_spec = None
    if strategy is not None:
        family = strategy.get("family")
        if not isinstance(family, str):
            errors.append(_error("STRATEGY_FAMILY_REQUIRED", "$.strategy.family", "strategy.family is required"))
        else:
            template_spec = get_template_spec(family)
            if template_spec is None:
                errors.append(_error("UNSUPPORTED_STRATEGY_FAMILY", "$.strategy.family", f"Unsupported strategy family: {family}"))
        _enum(strategy, "direction", SUPPORTED_DIRECTIONS, "$.strategy.direction", errors)
        _enum(strategy, "timeframe", SUPPORTED_TIMEFRAMES, "$.strategy.timeframe", errors)

    if universe is not None:
        _enum(universe, "market", SUPPORTED_MARKETS, "$.universe.market", errors)
        symbols = universe.get("symbols")
        if not isinstance(symbols, list) or not symbols or not all(isinstance(item, str) and item.strip() for item in symbols):
            errors.append(_error("SYMBOLS_REQUIRED", "$.universe.symbols", "universe.symbols must contain at least one symbol"))

    signal_names = set()
    if not isinstance(signals, list) or not signals:
        errors.append(_error("SIGNALS_REQUIRED", "$.signals", "signals must contain at least one signal"))
    else:
        for index, signal in enumerate(signals):
            path = f"$.signals[{index}]"
            if not isinstance(signal, dict):
                errors.append(_error("SIGNAL_TYPE", path, "signal must be an object"))
                continue
            name = signal.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(_error("SIGNAL_NAME_REQUIRED", f"{path}.name", "signal.name is required"))
            else:
                signal_names.add(name)
            indicator = signal.get("indicator")
            if not isinstance(indicator, str) or not indicator.strip():
                errors.append(_error("INDICATOR_REQUIRED", f"{path}.indicator", "signal.indicator is required"))
            elif template_spec and indicator not in template_spec.allowed_indicators:
                errors.append(_error("UNSUPPORTED_INDICATOR", f"{path}.indicator", f"Unsupported indicator for family: {indicator}"))
            window = signal.get("window")
            if not isinstance(window, int) or window < 2 or window > 500:
                errors.append(_error("INVALID_WINDOW", f"{path}.window", "signal.window must be an integer between 2 and 500"))
            right = signal.get("right")
            if right is not None and (not isinstance(right, str) or not right.strip()):
                errors.append(_error("INVALID_SIGNAL_REFERENCE", f"{path}.right", "signal.right must be a signal name"))

        for index, signal in enumerate(signals):
            if isinstance(signal, dict) and signal.get("right") and signal["right"] not in signal_names:
                errors.append(_error("UNKNOWN_SIGNAL_REFERENCE", f"$.signals[{index}].right", f"Unknown signal reference: {signal['right']}"))

    if risk is not None:
        _pct(risk, "max_drawdown_pct", "$.risk.max_drawdown_pct", errors, minimum=0, maximum=100, required=False)
        _pct(risk, "stop_loss_pct", "$.risk.stop_loss_pct", errors, minimum=0, maximum=100, required=False)
        _pct(risk, "take_profit_pct", "$.risk.take_profit_pct", errors, minimum=0, maximum=100, required=False)
        _pct(risk, "max_position_pct", "$.risk.max_position_pct", errors, minimum=0, maximum=100, required=True)

    if execution is not None:
        _enum(execution, "rebalance", SUPPORTED_REBALANCE, "$.execution.rebalance", errors)
        max_orders = execution.get("max_orders_per_day")
        if max_orders is not None and (not isinstance(max_orders, int) or max_orders < 0):
            errors.append(_error("INVALID_MAX_ORDERS", "$.execution.max_orders_per_day", "max_orders_per_day must be a non-negative integer"))

    return fail_result(errors) if errors else pass_result()


def _object(qyir: dict, field: str, errors: list[VerificationError]) -> dict | None:
    value = qyir.get(field)
    if not isinstance(value, dict):
        errors.append(_error("OBJECT_REQUIRED", f"$.{field}", f"{field} must be an object"))
        return None
    return value


def _enum(source: dict, key: str, allowed: set[str], path: str, errors: list[VerificationError]) -> None:
    value = source.get(key)
    if value not in allowed:
        errors.append(_error("INVALID_ENUM", path, f"{path} must be one of: {', '.join(sorted(allowed))}"))


def _pct(
    source: dict,
    key: str,
    path: str,
    errors: list[VerificationError],
    *,
    minimum: float,
    maximum: float,
    required: bool,
) -> None:
    value = source.get(key)
    if value is None:
        if required:
            errors.append(_error("PERCENT_REQUIRED", path, f"{key} is required"))
        return
    if not isinstance(value, (int, float)) or value < minimum or value > maximum:
        errors.append(_error("INVALID_PERCENT", path, f"{key} must be between {minimum} and {maximum}"))


def _error(code: str, path: str, message: str) -> VerificationError:
    return verification_error(code, path, message, category="schema")

