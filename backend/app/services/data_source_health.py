import logging
from datetime import timedelta

from ..extensions import db
from ..models import DataSourceHealthStatus, User
from ..providers.joinquant import JoinQuantClient
from ..tasks.notification_tasks import send_email_notification
from ..utils.time import format_beijing_iso, now_utc

logger = logging.getLogger(__name__)

JQDATA_SOURCE_NAME = "jqdata"
JQDATA_SOURCE_LABEL = "JQData API"
JQDATA_PROBE_SYMBOL = "000001.XSHE"
JQDATA_PROBE_WINDOW_DAYS = 14

STATUS_LABELS = {
    "healthy": "正常",
    "unhealthy": "异常",
    "unknown": "未检测",
}

STATUS_COLORS = {
    "healthy": "green",
    "unhealthy": "red",
    "unknown": "gray",
}


def serialize_data_source_health_status(record):
    status = (getattr(record, "status", None) or "unknown").strip() or "unknown"
    return {
        "source_name": getattr(record, "source_name", JQDATA_SOURCE_NAME) or JQDATA_SOURCE_NAME,
        "status": status,
        "status_label": STATUS_LABELS.get(status, STATUS_LABELS["unknown"]),
        "status_color": STATUS_COLORS.get(status, STATUS_COLORS["unknown"]),
        "last_checked_at": format_beijing_iso(getattr(record, "last_checked_at", None)),
        "last_success_at": format_beijing_iso(getattr(record, "last_success_at", None)),
        "last_failure_at": format_beijing_iso(getattr(record, "last_failure_at", None)),
        "last_error_message": getattr(record, "last_error_message", None),
        "consecutive_failures": int(getattr(record, "consecutive_failures", 0) or 0),
    }


class DataSourceHealthService:
    def __init__(self, client=None, session=None):
        self.client = client or JoinQuantClient()
        self.session = session or db.session

    def get_status(self):
        return self.session.get(DataSourceHealthStatus, JQDATA_SOURCE_NAME)

    def get_status_payload(self):
        record = self.get_status()
        if record is None:
            record = DataSourceHealthStatus(
                source_name=JQDATA_SOURCE_NAME,
                status="unknown",
                consecutive_failures=0,
            )
        return serialize_data_source_health_status(record)

    def check_jqdata_health(self):
        checked_at = now_utc()
        record = self.get_status()
        if record is None:
            record = DataSourceHealthStatus(
                source_name=JQDATA_SOURCE_NAME,
                status="unknown",
                consecutive_failures=0,
            )
            self.session.add(record)

        previous_status = record.status or "unknown"

        try:
            self._probe(checked_at)
        except Exception as exc:
            self._mark_unhealthy(record, checked_at, previous_status, str(exc))
        else:
            self._mark_healthy(record, checked_at, previous_status)

        self.session.commit()
        self._notify_transition(record, previous_status)
        return serialize_data_source_health_status(record)

    def _probe(self, checked_at):
        end_date = checked_at.date()
        start_date = end_date - timedelta(days=JQDATA_PROBE_WINDOW_DAYS)
        self.client.fetch_daily_data(JQDATA_PROBE_SYMBOL, start_date, end_date)

    def _mark_unhealthy(self, record, checked_at, previous_status, error_message):
        record.status = "unhealthy"
        record.last_checked_at = checked_at
        record.last_failure_at = checked_at
        record.last_error_message = error_message
        record.consecutive_failures = 1 if previous_status != "unhealthy" else int(record.consecutive_failures or 0) + 1
        if previous_status != "unhealthy":
            record.last_notified_status = "unhealthy"

    def _mark_healthy(self, record, checked_at, previous_status):
        record.status = "healthy"
        record.last_checked_at = checked_at
        record.last_success_at = checked_at
        record.last_error_message = None
        record.consecutive_failures = 0
        if previous_status == "unhealthy":
            record.last_notified_status = "healthy"

    def _notify_transition(self, record, previous_status):
        if record.status == "unhealthy" and previous_status != "unhealthy":
            event_type = "data_source_alert"
            event_time = record.last_failure_at or record.last_checked_at
        elif record.status == "healthy" and previous_status == "unhealthy":
            event_type = "data_source_recovered"
            event_time = record.last_success_at or record.last_checked_at
        else:
            return

        recipients = (
            self.session.query(User)
            .filter(User.role == "admin")
            .filter(User.email.isnot(None))
            .filter(User.email != "")
            .all()
        )
        if not recipients:
            logger.warning("data source health changed but no admin recipients are configured")
            return

        context_data = {
            "source_name": JQDATA_SOURCE_LABEL,
            "checked_at": format_beijing_iso(record.last_checked_at),
            "target_id": f"{record.source_name}:{record.status}:{event_time.isoformat()}",
        }
        if event_type == "data_source_alert":
            context_data["error_message"] = record.last_error_message

        for recipient in recipients:
            send_email_notification.delay(
                user_id=recipient.id,
                event_type=event_type,
                context_data=context_data,
            )
