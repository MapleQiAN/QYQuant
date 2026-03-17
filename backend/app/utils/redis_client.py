import os
import threading
import time

try:
    import redis
except Exception:  # pragma: no cover - depends on runtime env
    redis = None


class _MemoryStore:
    def __init__(self):
        self._values = {}
        self._lock = threading.Lock()

    def _prune_if_needed(self, key):
        item = self._values.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at <= time.time():
            self._values.pop(key, None)
            return None
        return value

    def get(self, key):
        with self._lock:
            return self._prune_if_needed(key)

    def set(self, key, value, ttl=None):
        expires_at = time.time() + ttl if ttl else None
        with self._lock:
            self._values[key] = (str(value), expires_at)

    def delete(self, key):
        with self._lock:
            self._values.pop(key, None)

    def ttl(self, key):
        with self._lock:
            item = self._values.get(key)
            if item is None:
                return -2
            _, expires_at = item
            if expires_at is None:
                return -1
            remaining = int(expires_at - time.time())
            if remaining <= 0:
                self._values.pop(key, None)
                return -2
            return remaining

    def incr(self, key, ttl=None):
        with self._lock:
            current = self._prune_if_needed(key)
            next_value = int(current or "0") + 1
            expires_at = time.time() + ttl if ttl else None
            self._values[key] = (str(next_value), expires_at)
            return next_value

    def clear(self):
        with self._lock:
            self._values.clear()


class _RedisStore:
    def __init__(self, client):
        self._client = client

    def get(self, key):
        return self._client.get(key)

    def set(self, key, value, ttl=None):
        if ttl:
            self._client.setex(key, int(ttl), value)
        else:
            self._client.set(key, value)

    def delete(self, key):
        self._client.delete(key)

    def ttl(self, key):
        return self._client.ttl(key)

    def incr(self, key, ttl=None):
        value = self._client.incr(key)
        if ttl and value == 1:
            self._client.expire(key, int(ttl))
        return int(value)

    def clear(self):  # pragma: no cover - not used in production
        pass


class AuthStore:
    def __init__(self, backend):
        self._backend = backend

    @staticmethod
    def _code_key(phone):
        return f"sms:code:{phone}"

    @staticmethod
    def _throttle_key(phone):
        return f"sms:throttle:{phone}"

    @staticmethod
    def _fail_key(phone):
        return f"sms:fail:{phone}"

    @staticmethod
    def _blacklist_key(jti):
        return f"token:blacklist:{jti}"

    def set_verification_code(self, phone, code, ttl=300):
        self._backend.set(self._code_key(phone), code, ttl=ttl)

    def get_verification_code(self, phone):
        return self._backend.get(self._code_key(phone))

    def delete_verification_code(self, phone):
        self._backend.delete(self._code_key(phone))

    def mark_code_sent(self, phone, ttl=60):
        self._backend.set(self._throttle_key(phone), "1", ttl=ttl)

    def get_throttle_remaining(self, phone):
        ttl = self._backend.ttl(self._throttle_key(phone))
        return max(ttl, 0) if ttl > 0 else 0

    def increment_failed_attempts(self, phone, ttl=1800):
        return self._backend.incr(self._fail_key(phone), ttl=ttl)

    def get_failed_attempts(self, phone):
        value = self._backend.get(self._fail_key(phone))
        return int(value or "0")

    def reset_failed_attempts(self, phone):
        self._backend.delete(self._fail_key(phone))

    def blacklist_token(self, jti, ttl):
        if ttl > 0:
            self._backend.set(self._blacklist_key(jti), "1", ttl=ttl)

    def is_token_blacklisted(self, jti):
        return self._backend.get(self._blacklist_key(jti)) == "1"

    def clear(self):
        self._backend.clear()


_auth_store = None
_auth_store_lock = threading.Lock()


def _build_backend():
    url = os.getenv("REDIS_URL")
    if url and redis is not None:
        try:
            client = redis.Redis.from_url(url, decode_responses=True)
            client.ping()
            return _RedisStore(client)
        except Exception:  # pragma: no cover - depends on runtime env
            pass
    return _MemoryStore()


def get_auth_store():
    global _auth_store
    if _auth_store is None:
        with _auth_store_lock:
            if _auth_store is None:
                _auth_store = AuthStore(_build_backend())
    return _auth_store


def reset_auth_store():
    global _auth_store
    with _auth_store_lock:
        _auth_store = AuthStore(_MemoryStore())
    return _auth_store
