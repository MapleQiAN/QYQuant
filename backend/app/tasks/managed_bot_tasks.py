import logging

from flask import has_app_context

from ..celery_app import celery_app
from ..services.managed_bot_execution import run_managed_bots_dry_run


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.managed_bot_tasks.run_managed_bots_dry_run")
def run_managed_bots_dry_run_task(self):
    if has_app_context():
        result = run_managed_bots_dry_run()
        logger.info("[managed-bot] dry-run result=%s", result)
        return result

    from .. import create_app

    app = create_app()
    with app.app_context():
        result = run_managed_bots_dry_run()
        logger.info("[managed-bot] dry-run result=%s", result)
        return result
