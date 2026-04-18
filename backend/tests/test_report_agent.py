def test_backtest_report_row_belongs_to_completed_job(app):
    from app.extensions import db
    from app.models import BacktestJob, BacktestJobStatus, BacktestReport, User

    with app.app_context():
        user = User(phone="13800138901", nickname="ReportOwner")
        db.session.add(user)
        db.session.flush()

        job = BacktestJob(
            user_id=user.id,
            status=BacktestJobStatus.COMPLETED.value,
            params={"symbol": "BTCUSDT"},
        )
        db.session.add(job)
        db.session.flush()

        report = BacktestReport(backtest_job_id=job.id, user_id=user.id, status="pending")
        db.session.add(report)
        db.session.commit()

        stored = BacktestReport.query.filter_by(backtest_job_id=job.id).one()
        assert stored.user_id == user.id
        assert stored.status == "pending"
