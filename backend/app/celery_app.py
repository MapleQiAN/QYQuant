import os
from urllib.parse import urlparse, urlunparse

from celery import Celery


def _is_eager():
    return os.getenv('CELERY_TASK_ALWAYS_EAGER', '').lower() in {'1', 'true', 'yes'}


def _replace_redis_db(url, db_index):
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme not in {'redis', 'rediss'}:
        return url
    return urlunparse(parsed._replace(path=f'/{db_index}'))


def _celery_url(env_name, default_db):
    explicit = os.getenv(env_name)
    if explicit:
        return explicit
    return _replace_redis_db(os.getenv('REDIS_URL'), default_db)


if _is_eager():
    celery_app = Celery('qyquant', broker='memory://', backend='cache+memory://')
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    celery_app.conf.task_store_eager_result = True
else:
    broker = _celery_url('CELERY_BROKER_URL', 1)
    backend = _celery_url('CELERY_RESULT_BACKEND', 1)
    celery_app = Celery('qyquant', broker=broker, backend=backend)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    worker_concurrency=int(os.getenv('CELERYD_CONCURRENCY', '10')),
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '300')),
    task_time_limit=int(os.getenv('CELERY_TASK_TIME_LIMIT', '330')),
    task_default_queue='default',
    task_routes={
        'app.tasks.backtests.*': {'queue': 'backtest'},
    },
)
