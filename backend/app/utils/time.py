import time
from datetime import datetime, timezone


def now_ms():
    return int(time.time() * 1000)


def now_utc():
    return datetime.now(timezone.utc)
