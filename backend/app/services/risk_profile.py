"""Risk profile builder for strategy generation.

Takes form data from the user and produces a structured RiskProfile
used by the strategy generator to adjust parameters like stop-loss,
position sizing, and signal filtering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DrawdownTolerance = Literal["low", "medium", "high"]
InvestmentStyle = Literal["conservative", "balanced", "aggressive"]


@dataclass(frozen=True)
class RiskProfile:
    max_single_loss_pct: float
    position_ratio: float
    drawdown_tolerance: DrawdownTolerance
    consecutive_loss_patience: int
    style: InvestmentStyle

    def to_dict(self) -> dict:
        return {
            "max_single_loss_pct": self.max_single_loss_pct,
            "position_ratio": self.position_ratio,
            "drawdown_tolerance": self.drawdown_tolerance,
            "consecutive_loss_patience": self.consecutive_loss_patience,
            "style": self.style,
        }


_DRAWDOWN_MAP = {
    "low": (0.05, 0.10),
    "medium": (0.10, 0.20),
    "high": (0.20, 0.30),
}

_STYLE_MAP = {
    "conservative": {
        "stop_loss_ratio": 0.02,
        "position_size": 0.2,
        "signal_filter_strength": "strong",
    },
    "balanced": {
        "stop_loss_ratio": 0.05,
        "position_size": 0.4,
        "signal_filter_strength": "moderate",
    },
    "aggressive": {
        "stop_loss_ratio": 0.10,
        "position_size": 0.8,
        "signal_filter_strength": "weak",
    },
}


def build_risk_profile(
    *,
    max_single_loss_pct: float,
    position_ratio: float,
    drawdown_tolerance: str,
    consecutive_loss_patience: int,
    style: str,
) -> RiskProfile:
    """Build a RiskProfile from user form data.

    Args:
        max_single_loss_pct: 1.0-10.0, max acceptable single loss percentage.
        position_ratio: 0.1-1.0, fraction of capital to deploy.
        drawdown_tolerance: "low", "medium", or "high".
        consecutive_loss_patience: 2-10, how many losing trades before pause.
        style: "conservative", "balanced", or "aggressive".

    Returns:
        Validated RiskProfile instance.
    """
    loss_pct = _clamp(float(max_single_loss_pct), 1.0, 10.0)
    pos_ratio = _clamp(float(position_ratio), 0.1, 1.0)
    tolerance = _validate_choice(str(drawdown_tolerance).lower(), _DRAWDOWN_MAP, "medium")
    patience = int(_clamp(int(consecutive_loss_patience), 2, 10))
    investment_style = _validate_choice(str(style).lower(), _STYLE_MAP, "balanced")

    return RiskProfile(
        max_single_loss_pct=loss_pct,
        position_ratio=pos_ratio,
        drawdown_tolerance=tolerance,
        consecutive_loss_patience=patience,
        style=investment_style,
    )


def risk_profile_to_generator_context(profile: RiskProfile) -> dict:
    """Convert RiskProfile into context for the strategy generator prompt."""
    style_params = _STYLE_MAP[profile.style]
    drawdown_range = _DRAWDOWN_MAP[profile.drawdown_tolerance]

    return {
        "stop_loss_ratio": style_params["stop_loss_ratio"],
        "position_size": style_params["position_size"],
        "signal_filter_strength": style_params["signal_filter_strength"],
        "max_drawdown_alert": drawdown_range[1],
        "max_single_loss_pct": profile.max_single_loss_pct / 100.0,
        "position_ratio": profile.position_ratio,
        "consecutive_loss_patience": profile.consecutive_loss_patience,
    }


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _validate_choice(value, valid_map, default):
    if value in valid_map:
        return value
    return default
