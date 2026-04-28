from __future__ import annotations

SUPPORTED_CLASSIFICATIONS = {"supported", "ambiguous", "unsupported", "unsafe"}
SUPPORTED_DIRECTIONS = {"long_only", "flat_or_long"}
SUPPORTED_TIMEFRAMES = {"1d", "4h", "1h", "15m"}
SUPPORTED_MARKETS = {"crypto", "gold", "stock", "futures"}
SUPPORTED_REBALANCE = {"on_signal", "daily", "weekly", "monthly"}


REQUIRED_TOP_LEVEL_FIELDS = {
    "version",
    "intent",
    "strategy",
    "universe",
    "signals",
    "risk",
    "execution",
}

