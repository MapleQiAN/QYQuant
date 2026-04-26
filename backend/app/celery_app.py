import os
from urllib.parse import urlparse, urlunparse

from celery import Celery
from celery.schedules import crontab


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


def _build_eager_celery_app():
    os.environ['CELERY_BROKER_URL'] = 'memory://'
    os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
    app = Celery('qyquant', broker='memory://', backend='cache+memory://')
    app.conf.update(
        broker_url='memory://',
        result_backend='cache+memory://',
        task_always_eager=True,
        task_eager_propagates=False,
        task_store_eager_result=False,
    )
    return app


if _is_eager():
    celery_app = _build_eager_celery_app()
else:
    broker = _celery_url('CELERY_BROKER_URL', 1)
    backend = _celery_url('CELERY_RESULT_BACKEND', 1)
    celery_app = Celery('qyquant', broker=broker, backend=backend)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    imports=(
        'app.tasks.backtests',
        'app.tasks.data_source_tasks',
        'app.tasks.notification_tasks',
        'app.tasks.report_generation',
        'app.tasks.review_tasks',
        'app.tasks.simulation_tasks',
        'app.tasks.quota_tasks',
    ),
    worker_concurrency=int(os.getenv('CELERYD_CONCURRENCY', '10')),
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '300')),
    task_time_limit=int(os.getenv('CELERY_TASK_TIME_LIMIT', '330')),
    task_default_queue='default',
    task_routes={
        'app.tasks.backtests.*': {'queue': 'backtest'},
        'app.tasks.notification_tasks.*': {'queue': 'notification'},
        'app.tasks.report_generation.*': {'queue': 'backtest'},
        'app.tasks.review_tasks.*': {'queue': 'review'},
        'app.tasks.simulation_tasks.*': {'queue': 'simulation'},
    },
    timezone='UTC',
)

celery_app.conf.beat_schedule = {
    'run-daily-simulation': {
        'task': 'app.tasks.simulation_tasks.run_daily_simulation',
        'schedule': crontab(hour=8, minute=0),
        'options': {'queue': 'simulation'},
    },
    'reset-monthly-quotas': {
        'task': 'app.tasks.quota_tasks.reset_monthly_quotas',
        'schedule': crontab(day_of_month='1', hour=0, minute=0),
        'options': {'queue': 'default'},
    },
    'check-jqdata-health': {
        'task': 'app.tasks.data_source_tasks.check_jqdata_health',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default'},
    },
}
