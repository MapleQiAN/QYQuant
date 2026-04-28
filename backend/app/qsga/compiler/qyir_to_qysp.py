from __future__ import annotations

import json
import shutil
import uuid
from copy import deepcopy
from pathlib import Path

from qysp.validator import validate

from .template_registry import TemplateSpec, get_template_spec


class QYIRCompileError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def compile_qyir_to_qysp_project(qyir: dict, output_dir: str | Path) -> Path:
    family = ((qyir.get("strategy") or {}).get("family") or "").strip()
    spec = get_template_spec(family)
    if spec is None:
        raise QYIRCompileError("UNSUPPORTED_STRATEGY_FAMILY", f"Unsupported strategy family: {family}")

    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    (output_path / "src").mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(qyir, spec)
    (output_path / "strategy.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(spec.template_dir / "strategy.py", output_path / "src" / "strategy.py")

    validation = validate(output_path)
    if not validation["valid"]:
        raise QYIRCompileError("QYSP_VALIDATION_FAILED", "Compiled QYSP project is invalid", {"errors": validation["errors"]})
    return output_path


def _build_manifest(qyir: dict, spec: TemplateSpec) -> dict:
    template_manifest = json.loads((spec.template_dir / "strategy.json").read_text(encoding="utf-8"))
    manifest = deepcopy(template_manifest)
    intent = qyir.get("intent") or {}
    strategy = qyir.get("strategy") or {}
    universe = qyir.get("universe") or {}
    risk = qyir.get("risk") or {}
    execution = qyir.get("execution") or {}
    signals = qyir.get("signals") or []

    manifest["id"] = str(uuid.uuid4())
    manifest["name"] = _strategy_name(intent, spec)
    manifest["description"] = intent.get("normalized_summary") or template_manifest.get("description") or "QSGA generated strategy draft"
    manifest["universe"] = {
        "symbols": universe.get("symbols") or [],
        "market": universe.get("market"),
    }
    manifest["data"] = {
        "resolution": strategy.get("timeframe"),
        "fields": ["open", "high", "low", "close", "volume"],
        "lookback": _max_signal_window(signals),
    }
    manifest["execution"] = {
        "orderTypes": ["MARKET"],
        "priceType": execution.get("price_timing") or "next_bar",
        "maxOrdersPerDay": int(execution.get("max_orders_per_day", 2)),
    }
    manifest["risk"] = {
        "maxPositionPct": risk.get("max_position_pct"),
        "maxDrawdownPct": risk.get("max_drawdown_pct"),
        "stopLossPct": risk.get("stop_loss_pct"),
        "takeProfitPct": risk.get("take_profit_pct"),
    }
    manifest["ui"] = {
        **dict(manifest.get("ui") or {}),
        "category": spec.qysp_category,
        "difficulty": "beginner",
    }
    manifest["tags"] = ["qsga", spec.qysp_category]
    manifest["parameters"] = _parameters_from_qyir(manifest.get("parameters") or [], signals, risk, spec)
    return _drop_none(manifest)


def _parameters_from_qyir(template_parameters: list[dict], signals: list[dict], risk: dict, spec: TemplateSpec) -> list[dict]:
    parameters = deepcopy(template_parameters)
    windows = [signal.get("window") for signal in signals if isinstance(signal, dict) and isinstance(signal.get("window"), int)]
    if len(windows) >= 1:
        _set_default(parameters, spec.parameter_map["fast_window"], min(windows))
    if len(windows) >= 2:
        _set_default(parameters, spec.parameter_map["slow_window"], max(windows))
    _append_number_parameter(parameters, "max_position_pct", risk.get("max_position_pct"), 1, 100, "最大仓位百分比")
    _append_number_parameter(parameters, "stop_loss_pct", risk.get("stop_loss_pct"), 0, 100, "止损百分比")
    _append_number_parameter(parameters, "take_profit_pct", risk.get("take_profit_pct"), 0, 100, "止盈百分比")
    return parameters


def _set_default(parameters: list[dict], key: str, value: int) -> None:
    for parameter in parameters:
        if parameter.get("key") == key:
            parameter["default"] = value
            return


def _append_number_parameter(parameters: list[dict], key: str, value, minimum: int, maximum: int, description: str) -> None:
    if value is None or any(parameter.get("key") == key for parameter in parameters):
        return
    parameters.append(
        {
            "key": key,
            "type": "number",
            "default": value,
            "min": minimum,
            "max": maximum,
            "description": description,
        }
    )


def _strategy_name(intent: dict, spec: TemplateSpec) -> str:
    summary = str(intent.get("normalized_summary") or "").strip()
    if summary:
        return summary[:80]
    return f"QSGA {spec.qysp_category.title()} Strategy"


def _max_signal_window(signals: list[dict]) -> int:
    windows = [signal.get("window") for signal in signals if isinstance(signal, dict) and isinstance(signal.get("window"), int)]
    return max(windows) if windows else 0


def _drop_none(value):
    if isinstance(value, dict):
        return {key: _drop_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value

