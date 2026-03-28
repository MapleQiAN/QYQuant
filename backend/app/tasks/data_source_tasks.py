import logging

from ..celery_app import celery_app
from ..services.data_source_health import DataSourceHealthService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.data_source_tasks.check_jqdata_health")
def check_jqdata_health():
    result = DataSourceHealthService().check_jqdata_health()
    logger.info(
        "jqdata health check finished: status=%s consecutive_failures=%s",
        result["status"],
        result["consecutive_failures"],
    )
    return {
        "status": result["status"],
        "consecutive_failures": result["consecutive_failures"],
    }
