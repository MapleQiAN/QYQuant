"""Unit tests for qysp.indicators module."""

from __future__ import annotations

import pandas as pd
import pytest


class TestSMA:
    """Tests for sma() function."""

    def test_sma_basic(self):
        """SMA(period=3) values match pandas rolling(3).mean()."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(series, period=3)
        expected = series.rolling(3).mean()
        pd.testing.assert_series_equal(result, expected)

    def test_sma_nan_prefix(self):
        """First period-1 values are NaN."""
        from qysp.indicators import sma

        series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = sma(series, period=3)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert not pd.isna(result.iloc[2])

    def test_sma_period_equals_length(self):
        """When series length equals period, only last value is valid."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0])
        result = sma(series, period=3)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == pytest.approx(2.0)

    def test_sma_period_one(self):
        """SMA with period=1 returns the original series."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0])
        result = sma(series, period=1)
        pd.testing.assert_series_equal(result, series)

    def test_sma_default_period(self):
        """SMA default period is 20."""
        from qysp.indicators import sma

        series = pd.Series(range(25), dtype=float)
        result = sma(series)
        # First 19 values should be NaN
        assert pd.isna(result.iloc[18])
        assert not pd.isna(result.iloc[19])


class TestEMA:
    """Tests for ema() function."""

    def test_ema_basic(self):
        """EMA(period=3) values match pandas ewm(span=3, adjust=False).mean()."""
        from qysp.indicators import ema

        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ema(series, period=3)
        expected = series.ewm(span=3, adjust=False).mean()
        pd.testing.assert_series_equal(result, expected)

    def test_ema_starts_from_first(self):
        """EMA starts from first value (non-NaN)."""
        from qysp.indicators import ema

        series = pd.Series([10.0, 20.0, 30.0])
        result = ema(series, period=3)
        assert not pd.isna(result.iloc[0])


class TestParameterValidation:
    """Tests for parameter validation across all functions."""

    def test_period_zero_raises(self):
        """period=0 raises ValueError."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            sma(series, period=0)

    def test_period_negative_raises(self):
        """period=-5 raises ValueError."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            sma(series, period=-5)

    def test_empty_series_raises(self):
        """Empty Series input raises ValueError."""
        from qysp.indicators import sma

        with pytest.raises(ValueError):
            sma(pd.Series(dtype=float), period=3)

    def test_ema_period_zero_raises(self):
        """EMA with period=0 raises ValueError."""
        from qysp.indicators import ema

        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            ema(series, period=0)

    def test_ema_empty_series_raises(self):
        """EMA with empty Series raises ValueError."""
        from qysp.indicators import ema

        with pytest.raises(ValueError):
            ema(pd.Series(dtype=float), period=3)

    def test_atr_period_zero_raises(self):
        """ATR with period=0 raises ValueError."""
        from qysp.indicators import atr

        s = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            atr(s, s, s, period=0)

    def test_atr_empty_series_raises(self):
        """ATR with empty series raises ValueError."""
        from qysp.indicators import atr

        with pytest.raises(ValueError):
            atr(pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float))

    def test_bollinger_num_std_zero_raises(self):
        """Bollinger bands with num_std=0 raises ValueError."""
        from qysp.indicators import bollinger_bands

        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        with pytest.raises(ValueError):
            bollinger_bands(series, period=3, num_std=0)

    def test_bollinger_num_std_negative_raises(self):
        """Bollinger bands with num_std=-1 raises ValueError."""
        from qysp.indicators import bollinger_bands

        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        with pytest.raises(ValueError):
            bollinger_bands(series, period=3, num_std=-1.0)

    def test_period_float_raises(self):
        """period=2.5 (non-integer) raises ValueError."""
        from qysp.indicators import sma

        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            sma(series, period=2.5)  # type: ignore[arg-type]

    def test_cross_over_empty_raises(self):
        """cross_over with empty series raises ValueError."""
        from qysp.indicators import cross_over

        with pytest.raises(ValueError):
            cross_over(pd.Series(dtype=float), pd.Series(dtype=float))

    def test_cross_under_empty_raises(self):
        """cross_under with empty series raises ValueError."""
        from qysp.indicators import cross_under

        with pytest.raises(ValueError):
            cross_under(pd.Series(dtype=float), pd.Series(dtype=float))

    def test_cross_over_length_mismatch_raises(self):
        """cross_over with mismatched lengths raises ValueError."""
        from qysp.indicators import cross_over

        with pytest.raises(ValueError):
            cross_over(pd.Series([1.0, 2.0]), pd.Series([1.0]))

    def test_cross_under_length_mismatch_raises(self):
        """cross_under with mismatched lengths raises ValueError."""
        from qysp.indicators import cross_under

        with pytest.raises(ValueError):
            cross_under(pd.Series([1.0, 2.0]), pd.Series([1.0]))


class TestATR:
    """Tests for atr() function."""

    def test_atr_basic(self):
        """ATR calculation with manually verified True Range."""
        from qysp.indicators import atr

        high = pd.Series([12.0, 13.0, 14.0, 13.5, 15.0])
        low = pd.Series([10.0, 11.0, 12.0, 11.5, 13.0])
        close = pd.Series([11.0, 12.5, 13.0, 12.0, 14.5])

        result = atr(high, low, close, period=3)
        assert len(result) == 5
        # First value uses high-low only (no prev close)
        # TR[0] = 12-10 = 2.0 (prev_close is NaN, so max is high-low)
        # TR[1] = max(13-11, |13-11|, |11-11|) = max(2, 2, 0) = 2.0
        # TR[2] = max(14-12, |14-12.5|, |12-12.5|) = max(2, 1.5, 0.5) = 2.0
        # ATR[2] = mean(2.0, 2.0, 2.0) = 2.0
        assert result.iloc[2] == pytest.approx(2.0)

    def test_atr_series_length_mismatch(self):
        """high/low/close with different lengths raises ValueError."""
        from qysp.indicators import atr

        high = pd.Series([1.0, 2.0, 3.0])
        low = pd.Series([1.0, 2.0])
        close = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            atr(high, low, close)


class TestBollingerBands:
    """Tests for bollinger_bands() function."""

    def test_bollinger_bands_basic(self):
        """Middle = SMA, upper = middle + 2*std, lower = middle - 2*std."""
        from qysp.indicators import bollinger_bands, sma

        series = pd.Series([20.0, 21.0, 22.0, 21.5, 23.0, 22.5, 24.0, 23.5, 25.0, 24.5])
        upper, middle, lower = bollinger_bands(series, period=5)

        expected_middle = sma(series, period=5)
        pd.testing.assert_series_equal(middle, expected_middle)

        rolling_std = series.rolling(5).std()
        expected_upper = expected_middle + 2.0 * rolling_std
        expected_lower = expected_middle - 2.0 * rolling_std
        pd.testing.assert_series_equal(upper, expected_upper)
        pd.testing.assert_series_equal(lower, expected_lower)

    def test_bollinger_bands_custom_std(self):
        """Custom num_std parameter works correctly."""
        from qysp.indicators import bollinger_bands, sma

        series = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0])
        upper, middle, lower = bollinger_bands(series, period=3, num_std=1.5)

        expected_middle = sma(series, period=3)
        rolling_std = series.rolling(3).std()
        expected_upper = expected_middle + 1.5 * rolling_std
        expected_lower = expected_middle - 1.5 * rolling_std
        pd.testing.assert_series_equal(upper, expected_upper)
        pd.testing.assert_series_equal(lower, expected_lower)

    def test_bollinger_bands_returns_tuple(self):
        """Returns a tuple of three Series."""
        from qysp.indicators import bollinger_bands

        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = bollinger_bands(series, period=3)
        assert isinstance(result, tuple)
        assert len(result) == 3
        for s in result:
            assert isinstance(s, pd.Series)


class TestCrossOver:
    """Tests for cross_over() function."""

    def test_cross_over_basic(self):
        """Detect s1 crossing above s2."""
        from qysp.indicators import cross_over

        s1 = pd.Series([1.0, 2.0, 4.0, 3.0])
        s2 = pd.Series([3.0, 3.0, 3.0, 3.0])
        result = cross_over(s1, s2)
        # At index 2: prev s1(2) <= prev s2(3) and curr s1(4) > s2(3) => True
        assert not result.iloc[0]
        assert not result.iloc[1]
        assert result.iloc[2]
        assert not result.iloc[3]

    def test_cross_over_no_cross(self):
        """Parallel Series, all False."""
        from qysp.indicators import cross_over

        s1 = pd.Series([1.0, 2.0, 3.0])
        s2 = pd.Series([5.0, 6.0, 7.0])
        result = cross_over(s1, s2)
        assert not result.any()

    def test_cross_over_first_element(self):
        """First element is always False."""
        from qysp.indicators import cross_over

        s1 = pd.Series([5.0, 6.0])
        s2 = pd.Series([1.0, 1.0])
        result = cross_over(s1, s2)
        assert not result.iloc[0]


class TestCrossUnder:
    """Tests for cross_under() function."""

    def test_cross_under_basic(self):
        """Detect s1 crossing below s2."""
        from qysp.indicators import cross_under

        s1 = pd.Series([4.0, 3.0, 2.0, 3.0])
        s2 = pd.Series([3.0, 3.0, 3.0, 3.0])
        result = cross_under(s1, s2)
        # At index 2: prev s1(3) >= prev s2(3) and curr s1(2) < s2(3) => True
        assert not result.iloc[0]
        assert not result.iloc[1]
        assert result.iloc[2]
        assert not result.iloc[3]

    def test_cross_under_no_cross(self):
        """Parallel Series, all False."""
        from qysp.indicators import cross_under

        s1 = pd.Series([5.0, 6.0, 7.0])
        s2 = pd.Series([1.0, 2.0, 3.0])
        result = cross_under(s1, s2)
        assert not result.any()


class TestPublicImports:
    """Tests for public API imports."""

    def test_public_imports(self):
        """All indicator functions importable from qysp."""
        from qysp import sma, ema, atr, bollinger_bands, cross_over, cross_under

        assert callable(sma)
        assert callable(ema)
        assert callable(atr)
        assert callable(bollinger_bands)
        assert callable(cross_over)
        assert callable(cross_under)
