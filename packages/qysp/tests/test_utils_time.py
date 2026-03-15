"""tests for qysp.utils.time — 时区工具函数。"""

from datetime import datetime, timezone

import pytest

from qysp.utils.time import BEIJING_TZ, now_beijing, to_beijing


class TestBeijingTZ:
    """BEIJING_TZ 常量测试。"""

    def test_beijing_tz_is_asia_shanghai(self) -> None:
        assert str(BEIJING_TZ) == "Asia/Shanghai"


class TestToBeijing:
    """to_beijing() 函数测试。"""

    def test_utc_to_beijing(self) -> None:
        utc_dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = to_beijing(utc_dt)
        assert result.hour == 18  # UTC+8
        assert result.tzinfo is not None

    def test_preserves_same_instant(self) -> None:
        utc_dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = to_beijing(utc_dt)
        # 同一时刻的 UTC 时间戳应相同
        assert result.timestamp() == utc_dt.timestamp()

    def test_midnight_utc_is_8am_beijing(self) -> None:
        utc_dt = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = to_beijing(utc_dt)
        assert result.hour == 8
        assert result.day == 1

    def test_rejects_naive_datetime(self) -> None:
        naive_dt = datetime(2024, 1, 15, 10, 0, 0)
        with pytest.raises(ValueError, match="naive datetime"):
            to_beijing(naive_dt)


class TestNowBeijing:
    """now_beijing() 函数测试。"""

    def test_returns_aware_datetime(self) -> None:
        result = now_beijing()
        assert result.tzinfo is not None

    def test_returns_beijing_timezone(self) -> None:
        result = now_beijing()
        # UTC offset should be +08:00
        offset = result.utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 8 * 3600

    def test_close_to_current_time(self) -> None:
        before = datetime.now(timezone.utc)
        result = now_beijing()
        after = datetime.now(timezone.utc)
        # 转换为 UTC 比较，应在 before 和 after 之间
        result_utc = result.astimezone(timezone.utc)
        assert before <= result_utc <= after
