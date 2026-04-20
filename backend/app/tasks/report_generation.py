from flask import has_app_context

from ..celery_app import celery_app
from ..report_agent.orchestrator import generate_report


@celery_app.task(bind=True, name="app.tasks.report_generation.generate_backtest_report")
def generate_backtest_report(self, job_id, user_id, force=False, locale="en"):
    if has_app_context():
        report = generate_report(job_id, user_id, force=force, locale=locale)
        return {"report_id": report.id, "status": report.status}

    from .. import create_app

    app = create_app()
    with app.app_context():
        report = generate_report(job_id, user_id, force=force, locale=locale)
        return {"report_id": report.id, "status": report.status}
