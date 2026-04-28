from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateSpec:
    family: str
    template_dir: Path
    qysp_category: str
    allowed_indicators: frozenset[str]
    parameter_map: dict[str, str]


def template_root() -> Path:
    return Path(__file__).resolve().parents[4] / "packages" / "qysp" / "src" / "qysp" / "templates"


TEMPLATE_REGISTRY = {
    "trend_following": TemplateSpec(
        family="trend_following",
        template_dir=template_root() / "trend_following",
        qysp_category="trend-following",
        allowed_indicators=frozenset({"ma"}),
        parameter_map={"fast_window": "fast_period", "slow_window": "slow_period"},
    ),
    "momentum": TemplateSpec(
        family="momentum",
        template_dir=template_root() / "momentum",
        qysp_category="momentum",
        allowed_indicators=frozenset({"ema", "ma", "return"}),
        parameter_map={"fast_window": "ema_period", "slow_window": "signal_period"},
    ),
}


def get_template_spec(family: str) -> TemplateSpec | None:
    return TEMPLATE_REGISTRY.get(family)
