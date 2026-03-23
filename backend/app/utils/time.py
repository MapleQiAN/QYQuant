import time
from datetime import datetime, timedelta, timezone

from qysp.utils.time import to_beijing


def now_ms():
    return int(time.time() * 1000)


def now_utc():
    return datetime.now(timezone.utc)


BEIJING_TZ = timezone(timedelta(hours=8))


def next_month_start_beijing(now=None):
    current = now.astimezone(BEIJING_TZ) if now is not None else datetime.now(BEIJING_TZ)
    year = current.year + (1 if current.month == 12 else 0)
    month = 1 if current.month == 12 else current.month + 1
    return datetime(year, month, 1, 0, 0, tzinfo=BEIJING_TZ)


def ensure_aware_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_beijing_iso(dt):
    if dt is None:
        return None
    return to_beijing(ensure_aware_utc(dt)).isoformat()


def format_beijing_iso_ms(value):
    if value is None:
        return None

    try:
        timestamp_ms = int(value)
    except (TypeError, ValueError):
        return None

    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return format_beijing_iso(dt)
