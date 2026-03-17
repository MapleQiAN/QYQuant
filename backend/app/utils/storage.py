import json
import os
from pathlib import Path


def build_backtest_storage_key(job_id):
    return f"backtest-results/{job_id}"


def write_json(key, payload):
    path = _storage_root() / _normalize_key(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return key


def read_json(key):
    path = _storage_root() / _normalize_key(key)
    return json.loads(path.read_text(encoding="utf-8"))


def _storage_root():
    configured = os.getenv("BACKTEST_STORAGE_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "storage"


def _normalize_key(key):
    return str(key).strip("/\\")
