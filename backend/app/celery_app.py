import os

from celery import Celery


def _is_eager():
    return os.getenv('CELERY_TASK_ALWAYS_EAGER', '').lower() in {'1', 'true', 'yes'}


if _is_eager():
    celery_app = Celery('qyquant', broker='memory://', backend='cache+memory://')
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.task_store_eager_result = True
else:
    broker = os.getenv('REDIS_URL')
    celery_app = Celery('qyquant', broker=broker, backend=broker)
