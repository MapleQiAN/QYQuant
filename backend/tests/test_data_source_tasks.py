from datetime import datetime, timezone

from app.extensions import db
from app.models import DataSourceHealthStatus, User
from app.providers.joinquant import JoinQuantAPIError


class _StubJoinQuantClient:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def fetch_daily_data(self, symbol, start_date, end_date):
        self.calls.append((symbol, start_date, end_date))
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _seed_admin(app, *, email="admin@example.com"):
    with app.app_context():
        admin = User(
            phone="13800138950",
            nickname="HealthAdmin",
            role="admin",
            email=email,
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


def test_check_jqdata_health_marks_source_healthy_on_first_success(app, monkeypatch):
    from app.services.data_source_health import DataSourceHealthService

    delay_calls = []
    client = _StubJoinQuantClient([])

    monkeypatch.setattr(
        "app.services.data_source_health.send_email_notification",
        type("DelayStub", (), {"delay": staticmethod(lambda **kwargs: delay_calls.append(kwargs))}),
    )

    with app.app_context():
        service = DataSourceHealthService(client=client, session=db.session)
        result = service.check_jqdata_health()

        status = db.session.get(DataSourceHealthStatus, "jqdata")
        assert status is not None
        assert status.status == "healthy"
        assert status.last_checked_at is not None
        assert status.last_success_at is not None
        assert status.last_failure_at is None
        assert status.last_error_message is None
        assert status.consecutive_failures == 0
        assert status.last_notified_status is None

    assert result["status"] == "healthy"
    assert delay_calls == []
    assert client.calls[0][0] == "000001.XSHE"


def test_check_jqdata_health_marks_source_unhealthy_and_notifies_admins(app, monkeypatch):
    from app.services.data_source_health import DataSourceHealthService

    admin_id = _seed_admin(app)
    delay_calls = []
    client = _StubJoinQuantClient(JoinQuantAPIError("request timed out"))

    monkeypatch.setattr(
        "app.services.data_source_health.send_email_notification",
        type("DelayStub", (), {"delay": staticmethod(lambda **kwargs: delay_calls.append(kwargs))}),
    )

    with app.app_context():
        service = DataSourceHealthService(client=client, session=db.session)
        result = service.check_jqdata_health()

        status = db.session.get(DataSourceHealthStatus, "jqdata")
        assert status is not None
        assert status.status == "unhealthy"
        assert status.last_checked_at is not None
        assert status.last_success_at is None
        assert status.last_failure_at is not None
        assert status.last_error_message == "request timed out"
        assert status.consecutive_failures == 1
        assert status.last_notified_status == "unhealthy"

    assert result["status"] == "unhealthy"
    assert len(delay_calls) == 1
    assert delay_calls[0]["user_id"] == admin_id
    assert delay_calls[0]["event_type"] == "data_source_alert"
    assert delay_calls[0]["context_data"]["source_name"] == "JQData API"
    assert delay_calls[0]["context_data"]["target_id"].startswith("jqdata:unhealthy:")


def test_check_jqdata_health_does_not_repeat_alert_for_continuous_failures(app, monkeypatch):
    from app.services.data_source_health import DataSourceHealthService

    _seed_admin(app)
    delay_calls = []
    client = _StubJoinQuantClient(
        JoinQuantAPIError("request timed out"),
        JoinQuantAPIError("authentication failed"),
    )

    monkeypatch.setattr(
        "app.services.data_source_health.send_email_notification",
        type("DelayStub", (), {"delay": staticmethod(lambda **kwargs: delay_calls.append(kwargs))}),
    )

    with app.app_context():
        service = DataSourceHealthService(client=client, session=db.session)
        first = service.check_jqdata_health()
        second = service.check_jqdata_health()

        status = db.session.get(DataSourceHealthStatus, "jqdata")
        assert status is not None
        assert status.status == "unhealthy"
        assert status.consecutive_failures == 2
        assert status.last_error_message == "authentication failed"
        assert status.last_notified_status == "unhealthy"

    assert first["status"] == "unhealthy"
    assert second["status"] == "unhealthy"
    assert len(delay_calls) == 1


def test_check_jqdata_health_sends_recovery_notification_after_failure(app, monkeypatch):
    from app.services.data_source_health import DataSourceHealthService

    _seed_admin(app)
    delay_calls = []
    client = _StubJoinQuantClient(JoinQuantAPIError("request timed out"), [])

    monkeypatch.setattr(
        "app.services.data_source_health.send_email_notification",
        type("DelayStub", (), {"delay": staticmethod(lambda **kwargs: delay_calls.append(kwargs))}),
    )

    with app.app_context():
        service = DataSourceHealthService(client=client, session=db.session)
        service.check_jqdata_health()
        result = service.check_jqdata_health()

        status = db.session.get(DataSourceHealthStatus, "jqdata")
        assert status is not None
        assert status.status == "healthy"
        assert status.last_success_at is not None
        assert status.last_error_message is None
        assert status.consecutive_failures == 0
        assert status.last_notified_status == "healthy"

    assert result["status"] == "healthy"
    assert [call["event_type"] for call in delay_calls] == [
        "data_source_alert",
        "data_source_recovered",
    ]
    assert delay_calls[1]["context_data"]["target_id"].startswith("jqdata:healthy:")


def test_check_jqdata_health_task_is_registered_every_five_minutes():
    from app.celery_app import celery_app

    assert "app.tasks.data_source_tasks" in celery_app.conf.imports

    schedule = celery_app.conf.beat_schedule["check-jqdata-health"]
    assert schedule["task"] == "app.tasks.data_source_tasks.check_jqdata_health"
    assert schedule["options"] == {"queue": "default"}
    assert schedule["schedule"]._orig_minute == "*/5"


def test_check_jqdata_health_task_returns_latest_status_payload(monkeypatch):
    from app.tasks.data_source_tasks import check_jqdata_health

    monkeypatch.setattr(
        "app.tasks.data_source_tasks.DataSourceHealthService",
        type(
            "ServiceStub",
            (),
            {
                "__init__": lambda self: None,
                "check_jqdata_health": lambda self: {
                    "status": "unhealthy",
                    "consecutive_failures": 3,
                },
            },
        ),
    )

    result = check_jqdata_health.run()

    assert result == {"status": "unhealthy", "consecutive_failures": 3}
