import logging
import os
import threading
import time

from celery.utils.log import get_task_logger
from flask import has_app_context
from flask_mail import Message

from ..celery_app import celery_app
from ..extensions import db, mail
from ..models import User
from ..utils.email_templates import render_strategy_review_email

logger = get_task_logger(__name__) if logging.getLogger().handlers else logging.getLogger(__name__)

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class _MemoryIdempotencyStore:
    def __init__(self):
        self._values = {}
        self._lock = threading.Lock()

    def claim(self, key, ttl):
        now = time.time()
        with self._lock:
            expires_at = self._values.get(key)
            if expires_at is not None and expires_at > now:
                return False
            self._values[key] = now + ttl
            return True

    def release(self, key):
        with self._lock:
            self._values.pop(key, None)


class _RedisIdempotencyStore:
    def __init__(self, client):
        self._client = client

    def claim(self, key, ttl):
        return bool(self._client.set(key, 1, nx=True, ex=int(ttl)))

    def release(self, key):
        self._client.delete(key)


_idempotency_store = None
_idempotency_lock = threading.Lock()


def _build_idempotency_store():
    url = os.getenv('REDIS_URL')
    if url and redis is not None:
        try:
            client = redis.Redis.from_url(url, decode_responses=True)
            client.ping()
            return _RedisIdempotencyStore(client)
        except Exception:  # pragma: no cover
            pass
    return _MemoryIdempotencyStore()


def _get_idempotency_store():
    global _idempotency_store
    if _idempotency_store is None:
        with _idempotency_lock:
            if _idempotency_store is None:
                _idempotency_store = _build_idempotency_store()
    return _idempotency_store


def reset_email_idempotency_state():
    global _idempotency_store
    with _idempotency_lock:
        _idempotency_store = _MemoryIdempotencyStore()
    return _idempotency_store


def _delivery_key(event_type, target_id):
    return f"email_sent:{event_type}:{target_id}"


def _claim_delivery(event_type, target_id, ttl=86400):
    return _get_idempotency_store().claim(_delivery_key(event_type, target_id), ttl)


def _release_delivery(event_type, target_id):
    _get_idempotency_store().release(_delivery_key(event_type, target_id))


def _render_email(event_type, context_data):
    if event_type == 'strategy_review_result':
        return render_strategy_review_email(
            strategy_name=context_data['strategy_name'],
            status=context_data['status'],
            reason=context_data.get('reason'),
        )
    raise ValueError(f"Unsupported email notification event type: {event_type}")


def _retry_count(task):
    override = getattr(task, '_retry_count_override', None)
    if override is not None:
        return int(override)
    request = getattr(task, 'request', None)
    return int(getattr(request, 'retries', 0) or 0)


def _send_email_notification(self, user_id, event_type, context_data):
    user = db.session.get(User, user_id)
    if user is None:
        logger.error("email notification user missing: user_id=%s event_type=%s", user_id, event_type)
        return {'ok': False, 'skipped': True}

    recipient = getattr(user, 'email', None) or context_data.get('recipient_email')
    if not recipient:
        logger.error("email notification missing recipient: user_id=%s event_type=%s", user_id, event_type)
        return {'ok': False, 'skipped': True}

    target_id = str(context_data.get('target_id') or '')
    if target_id and not _claim_delivery(event_type, target_id):
        return {'ok': True, 'skipped': True}

    try:
        subject, body_html, body_text = _render_email(event_type, context_data)
        message = Message(
            subject=subject,
            recipients=[recipient],
            body=body_text,
            html=body_html,
        )
        mail.send(message)
        return {'ok': True, 'skipped': False}
    except Exception as exc:
        if target_id:
            _release_delivery(event_type, target_id)
        logger.error("email notification send failed: event_type=%s user_id=%s error=%s", event_type, user_id, exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** _retry_count(self)))


# 调用示例（策略审核结果通知）：
# from app.tasks.notification_tasks import send_email_notification
# send_email_notification.delay(
#     user_id=strategy.user_id,
#     event_type='strategy_review_result',
#     context_data={
#         'strategy_name': strategy.name,
#         'status': 'approved',
#         'reason': None,
#         'target_id': strategy.id,
#     }
# )
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.notification_tasks.send_email_notification')
def send_email_notification(self, user_id: str, event_type: str, context_data: dict):
    if has_app_context():
        return _send_email_notification(self, user_id, event_type, context_data)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _send_email_notification(self, user_id, event_type, context_data)
