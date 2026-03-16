"""Technical indicator functions for quantitative strategy development.

All functions accept and return pandas Series, using pandas built-in
rolling/ewm methods for computation. No external C dependencies (ta-lib).
"""

from __future__ import annotations

import pandas as pd


def _validate_series(series: pd.Series) -> None:
    """Validate that series is non-empty."""
    if len(series) == 0:
        raise ValueError("series must not be empty")


def _validate_period(period: int) -> None:
    """Validate that period is a positive integer."""
    if not isinstance(period, int):
        raise ValueError(f"period must be an integer, got {type(period).__name__}")
    if period <= 0:
        raise ValueError(f"period must be a positive integer, got {period}")


def sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average.

    Args:
        series: Price or value series.
        period: Lookback window size. Must be > 0.

    Returns:
        Series of same length with SMA values. First period-1 values are NaN.

    Raises:
        ValueError: If period <= 0 or series is empty.
    """
    _validate_period(period)
    _validate_series(series)
    return series.rolling(period).mean()


def ema(series: pd.Series, period: int = 20) -> pd.Series:
    """Exponential Moving Average.

    Args:
        series: Price or value series.
        period: EMA span. Must be > 0.

    Returns:
        Series of same length with EMA values. Starts from first element.

    Raises:
        ValueError: If period <= 0 or series is empty.
    """
    _validate_period(period)
    _validate_series(series)
    return series.ewm(span=period, adjust=False).mean()


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range.

    Args:
        high: High price series.
        low: Low price series.
        close: Close price series.
        period: Lookback window. Must be > 0.

    Returns:
        Series of same length with ATR values.

    Raises:
        ValueError: If period <= 0, any series is empty, or lengths mismatch.
    """
    _validate_period(period)
    _validate_series(high)
    _validate_series(low)
    _validate_series(close)
    if not (len(high) == len(low) == len(close)):
        raise ValueError(
            f"high, low, close must have same length, "
            f"got {len(high)}, {len(low)}, {len(close)}"
        )
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean()


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands.

    Args:
        series: Price or value series.
        period: SMA lookback window. Must be > 0.
        num_std: Number of standard deviations. Must be > 0.

    Returns:
        Tuple of (upper, middle, lower) bands as pandas Series.

    Raises:
        ValueError: If period <= 0, num_std <= 0, or series is empty.
    """
    _validate_period(period)
    _validate_series(series)
    if num_std <= 0:
        raise ValueError(f"num_std must be positive, got {num_std}")
    middle = sma(series, period)
    rolling_std = series.rolling(period).std()
    upper = middle + num_std * rolling_std
    lower = middle - num_std * rolling_std
    return upper, middle, lower


def cross_over(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Detect bullish crossover (s1 crosses above s2).

    Args:
        s1: First series.
        s2: Second series.

    Returns:
        Boolean Series. True where s1 crosses above s2
        (previous bar s1 <= s2 and current bar s1 > s2).
        First element is always False.

    Raises:
        ValueError: If either series is empty or lengths mismatch.
    """
    _validate_series(s1)
    _validate_series(s2)
    if len(s1) != len(s2):
        raise ValueError(
            f"s1 and s2 must have same length, got {len(s1)} and {len(s2)}"
        )
    prev_s1 = s1.shift(1)
    prev_s2 = s2.shift(1)
    crossed = (prev_s1 <= prev_s2) & (s1 > s2)
    crossed.iloc[0] = False
    return crossed


def cross_under(s1: pd.Series, s2: pd.Series) -> pd.Series:
    """Detect bearish crossover (s1 crosses below s2).

    Args:
        s1: First series.
        s2: Second series.

    Returns:
        Boolean Series. True where s1 crosses below s2
        (previous bar s1 >= s2 and current bar s1 < s2).
        First element is always False.

    Raises:
        ValueError: If either series is empty or lengths mismatch.
    """
    _validate_series(s1)
    _validate_series(s2)
    if len(s1) != len(s2):
        raise ValueError(
            f"s1 and s2 must have same length, got {len(s1)} and {len(s2)}"
        )
    prev_s1 = s1.shift(1)
    prev_s2 = s2.shift(1)
    crossed = (prev_s1 >= prev_s2) & (s1 < s2)
    crossed.iloc[0] = False
    return crossed
