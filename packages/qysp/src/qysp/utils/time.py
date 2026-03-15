"""时区工具函数 — 统一使用北京时间 (UTC+8)。"""

import zoneinfo
from datetime import datetime

BEIJING_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")


def to_beijing(dt: datetime) -> datetime:
    """将 datetime 转为北京时间（用于 API 输出）。

    Args:
        dt: 带时区信息的 datetime 对象。

    Returns:
        转换为北京时间的 datetime 对象。

    Raises:
        ValueError: 如果传入 naive datetime（无时区信息）。
    """
    if dt.tzinfo is None:
        raise ValueError("不允许使用 naive datetime，请提供带时区信息的 datetime")
    return dt.astimezone(BEIJING_TZ)


def now_beijing() -> datetime:
    """返回当前北京时间。

    Returns:
        当前北京时间的 datetime 对象。
    """
    return datetime.now(BEIJING_TZ)
