import json
import logging
import os
import threading
import time

try:
    import redis
except Exception:  # pragma: no cover - fallback when redis isn't installed
    redis = None


logger = logging.getLogger(__name__)


class CacheBackend:
    def get(self, key):
        raise NotImplementedError

    def set(self, key, value, ttl=None):
        raise NotImplementedError


class MemoryCache(CacheBackend):
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expires_at = item
            if expires_at is not None and expires_at <= now:
                del self._store[key]
                return None
            return value

    def set(self, key, value, ttl=None):
        expires_at = time.time() + ttl if ttl else None
        with self._lock:
            self._store[key] = (value, expires_at)


class RedisCache(CacheBackend):
    def __init__(self, client):
        self.client = client

    def get(self, key):
        return self.client.get(key)

    def set(self, key, value, ttl=None):
        if ttl:
            self.client.setex(key, int(ttl), value)
        else:
            self.client.set(key, value)


_cache_instance = None
_cache_lock = threading.Lock()


def _build_cache():
    url = os.getenv('REDIS_URL')
    if url and redis is not None:
        try:
            client = redis.Redis.from_url(url, decode_responses=True)
            client.ping()
            logger.info("Cache backend: redis")
            return RedisCache(client)
        except Exception:  # pragma: no cover - depends on runtime env
            logger.warning("Redis unavailable, falling back to memory cache")
    return MemoryCache()


def get_cache():
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = _build_cache()
    return _cache_instance


def cache_get_json(key):
    value = get_cache().get(key)
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def cache_set_json(key, value, ttl=None):
    payload = json.dumps(value, ensure_ascii=True, separators=(',', ':'), default=str)
    get_cache().set(key, payload, ttl=ttl)
