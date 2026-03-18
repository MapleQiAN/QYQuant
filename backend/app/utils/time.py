import time
from datetime import datetime, timezone

from qysp.utils.time import to_beijing


def now_ms():
    return int(time.time() * 1000)


def now_utc():
    return datetime.now(timezone.utc)


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
