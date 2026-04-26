import hashlib
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import (
    AuditLog,
    BacktestJob,
    BacktestJobStatus,
    DataSourceHealthStatus,
    File,
    Notification,
    RefreshToken,
    Report,
    Strategy,
    StrategyVersion,
    User,
)
from app.utils.time import now_utc


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, *, phone, nickname):
    _seed_code(client.application, phone)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": phone,
            "code": "123456",
            "nickname": nickname,
        },
    )
    assert response.status_code == 200
    return response.json["access_token"], response.json["data"]["user_id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_strategy_for_review(
    app,
    *,
    strategy_id,
    owner_id,
    name="Pending Strategy",
    title="Pending Strategy",
    description="Strategy waiting for review.",
    review_status="pending",
    is_public=False,
    created_at=1700000000000,
    updated_at=1700000000000,
    last_update=1700000000000,
):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            owner_id=owner_id,
            name=name,
            title=title,
            symbol="BTCUSDT",
            status="draft",
            description=description,
            category="trend-following",
            tags=["trend", "swing"],
            display_metrics={
                "sharpe_ratio": 1.32,
                "max_drawdown": -12.4,
                "total_return": 31.8,
            },
            review_status=review_status,
            is_public=is_public,
            created_at=created_at,
            updated_at=updated_at,
            last_update=last_update,
        )
        db.session.add(strategy)
        db.session.commit()
    return strategy_id


def _seed_review_artifacts(app, *, strategy_id, owner_id, tmp_path, checksum="review-checksum"):
    package_path = tmp_path / f"{strategy_id}.qys"
    package_bytes = b"review-package"
    package_path.write_bytes(package_bytes)
    expected_checksum = checksum if checksum is not None else hashlib.sha256(package_bytes).hexdigest()

    with app.app_context():
        file_record = File(
            owner_id=owner_id,
            filename=f"{strategy_id}-1.0.0.qys",
            content_type="application/zip",
            size=len(package_bytes),
            path=package_path.as_posix(),
        )
        db.session.add(file_record)
        db.session.flush()
        db.session.add(
            StrategyVersion(
                strategy_id=strategy_id,
                version="1.0.0",
                file_id=file_record.id,
                checksum=expected_checksum,
            )
        )
        db.session.add(
            BacktestJob(
                id=f"{strategy_id}-backtest",
                user_id=owner_id,
                strategy_id=strategy_id,
                status=BacktestJobStatus.COMPLETED.value,
                params={"symbol": "BTCUSDT", "timeframe": "1d"},
                result_summary={"sharpe_ratio": 1.32, "max_drawdown": -12.4, "total_return": 31.8},
                result_storage_key=f"backtests/{strategy_id}",
            )
        )
        db.session.commit()


def _seed_public_strategy_for_reports(
    app,
    *,
    strategy_id,
    owner_id,
    title="Reported Strategy",
    created_at=1700000000000,
):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            owner_id=owner_id,
            name=title,
            title=title,
            symbol="ETHUSDT",
            status="running",
            description="Public strategy under report review.",
            category="trend-following",
            tags=["trend", "reported"],
            display_metrics={
                "sharpe_ratio": 1.18,
                "max_drawdown": -7.9,
                "total_return": 18.4,
            },
            review_status="approved",
            is_public=True,
            created_at=created_at,
            updated_at=created_at,
            last_update=created_at,
        )
        db.session.add(strategy)
        db.session.commit()
    return strategy_id


def _seed_report(
    app,
    *,
    report_id,
    reporter_id,
    strategy_id,
    reason="Misleading claims in description.",
    status="pending",
    created_at=None,
):
    with app.app_context():
        report = Report(
            id=report_id,
            reporter_id=reporter_id,
            strategy_id=strategy_id,
            reason=reason,
            status=status,
            created_at=created_at or now_utc(),
        )
        db.session.add(report)
        db.session.commit()
    return report_id


def _seed_backtest_job(
    app,
    *,
    job_id,
    status,
    user_id=None,
    strategy_id=None,
    params=None,
    started_at=None,
    completed_at=None,
    created_at=None,
    error_message=None,
):
    with app.app_context():
        job = BacktestJob(
            id=job_id,
            user_id=user_id,
            strategy_id=strategy_id,
            status=status,
            params=params or {"symbol": "BTCUSDT"},
            started_at=started_at,
            completed_at=completed_at,
            created_at=created_at or now_utc(),
            error_message=error_message,
        )
        db.session.add(job)
        db.session.commit()
    return job_id


def test_admin_health_allows_admin_users(client, app):
    token, user_id = _login_user(client, phone="13800138201", nickname="AdminUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.role = "admin"
        db.session.commit()

    response = client.get("/api/v1/admin/health", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"] == {"status": "ok", "scope": "admin"}


def test_admin_health_rejects_non_admin_users(client):
    token, _ = _login_user(client, phone="13800138202", nickname="NormalUser")

    response = client.get("/api/v1/admin/health", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json["error"] == {
        "code": "FORBIDDEN",
        "message": "管理员权限不足",
    }


def test_admin_health_requires_auth(client):
    response = client.get("/api/v1/admin/health")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_admin_data_source_health_returns_unknown_before_first_check(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138204", nickname="HealthAdmin")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    response = client.get(
        "/api/v1/admin/data-source-health",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {
        "source_name": "jqdata",
        "status": "unknown",
        "status_label": "未检测",
        "status_color": "gray",
        "last_checked_at": None,
        "last_success_at": None,
        "last_failure_at": None,
        "last_error_message": None,
        "consecutive_failures": 0,
    }


def test_admin_data_source_health_serializes_unhealthy_status_for_admins(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138205", nickname="HealthReader")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.add(
            DataSourceHealthStatus(
                source_name="jqdata",
                status="unhealthy",
                last_checked_at=datetime(2026, 3, 27, 1, 0, tzinfo=timezone.utc),
                last_success_at=datetime(2026, 3, 27, 0, 30, tzinfo=timezone.utc),
                last_failure_at=datetime(2026, 3, 27, 1, 0, tzinfo=timezone.utc),
                last_error_message="request timed out",
                consecutive_failures=2,
                last_notified_status="unhealthy",
            )
        )
        db.session.commit()

    response = client.get(
        "/api/v1/admin/data-source-health",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {
        "source_name": "jqdata",
        "status": "unhealthy",
        "status_label": "异常",
        "status_color": "red",
        "last_checked_at": "2026-03-27T09:00:00+08:00",
        "last_success_at": "2026-03-27T08:30:00+08:00",
        "last_failure_at": "2026-03-27T09:00:00+08:00",
        "last_error_message": "request timed out",
        "consecutive_failures": 2,
    }


def test_admin_data_source_health_rejects_non_admin_users(client):
    token, _ = _login_user(client, phone="13800138206", nickname="PlainHealthUser")

    response = client.get(
        "/api/v1/admin/data-source-health",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"


def test_write_audit_log_persists_record(app):
    from app.utils.audit import write_audit_log

    with app.app_context():
        operator = User(id="audit-admin", phone="13800138203", nickname="AuditAdmin", role="admin")
        db.session.add(operator)
        db.session.commit()

        log = write_audit_log(
            operator_id=operator.id,
            action="admin_health_check",
            target_type="system",
            target_id="admin-dashboard",
            details={"source": "test"},
        )

        stored = db.session.get(AuditLog, log.id)
        assert stored is not None
        assert stored.operator_id == operator.id
        assert stored.action == "admin_health_check"
        assert stored.target_type == "system"
        assert stored.target_id == "admin-dashboard"
        assert stored.details == {"source": "test"}


def test_admin_strategy_review_queue_lists_pending_only_for_admins(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138211", nickname="ReviewAdmin")
    _, owner_id = _login_user(client, phone="13800138212", nickname="StrategyAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        owner = db.session.get(User, owner_id)
        admin.role = "admin"
        owner.nickname = "量化作者"
        db.session.commit()

    _seed_strategy_for_review(
        app,
        strategy_id="pending-newer",
        owner_id=owner_id,
        title="Newer Pending Strategy",
        created_at=1700000002000,
    )
    _seed_strategy_for_review(
        app,
        strategy_id="pending-older",
        owner_id=owner_id,
        title="Older Pending Strategy",
        created_at=1700000001000,
    )
    _seed_strategy_for_review(
        app,
        strategy_id="approved-hidden",
        owner_id=owner_id,
        title="Approved Strategy",
        review_status="approved",
        is_public=True,
        created_at=1700000003000,
    )

    response = client.get(
        "/api/v1/admin/strategies?review_status=pending&page=1&per_page=20",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]] == ["pending-newer", "pending-older"]
    assert response.json["meta"] == {"total": 2, "page": 1, "per_page": 20}
    assert response.json["data"][0] == {
        "id": "pending-newer",
        "title": "Newer Pending Strategy",
        "name": "Pending Strategy",
        "description": "Strategy waiting for review.",
        "category": "trend-following",
        "tags": ["trend", "swing"],
        "display_metrics": {
            "sharpe_ratio": 1.32,
            "max_drawdown": -12.4,
            "total_return": 31.8,
        },
        "owner_id": owner_id,
        "author_nickname": "量化作者",
        "created_at": "2023-11-15T06:13:22+08:00",
        "review_status": "pending",
    }


def test_admin_strategy_review_queue_rejects_non_admin_users(client, app):
    token, user_id = _login_user(client, phone="13800138213", nickname="PlainUser")
    _seed_strategy_for_review(app, strategy_id="pending-forbidden", owner_id=user_id)

    response = client.get(
        "/api/v1/admin/strategies?review_status=pending&page=1&per_page=20",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json["error"] == {
        "code": "FORBIDDEN",
        "message": "管理员权限不足",
    }


def test_admin_strategy_review_packet_returns_evidence_for_admin(client, app, tmp_path):
    admin_token, admin_id = _login_user(client, phone="13800138230", nickname="ReviewPacketAdmin")
    _, owner_id = _login_user(client, phone="13800138231", nickname="ReviewPacketAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_strategy_for_review(app, strategy_id="pending-packet", owner_id=owner_id)
    _seed_review_artifacts(app, strategy_id="pending-packet", owner_id=owner_id, tmp_path=tmp_path)

    response = client.get(
        "/api/v1/admin/strategies/pending-packet/review-packet",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["strategy"]["id"] == "pending-packet"
    assert data["version"]["version"] == "1.0.0"
    assert data["version"]["filename"] == "pending-packet-1.0.0.qys"
    assert data["version"]["checksum"] == "review-checksum"
    assert data["version"]["checksum_valid"] is False
    assert data["latest_backtest"] == {
        "id": "pending-packet-backtest",
        "status": "completed",
        "params": {"symbol": "BTCUSDT", "timeframe": "1d"},
        "result_summary": {"sharpe_ratio": 1.32, "max_drawdown": -12.4, "total_return": 31.8},
        "result_storage_key": "backtests/pending-packet",
    }
    assert data["checks"] == {
        "has_version": True,
        "has_package_file": True,
        "checksum_valid": False,
        "has_completed_backtest": True,
    }


def test_admin_strategy_review_approve_requires_review_artifacts(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138232", nickname="ReviewGuardAdmin")
    _, owner_id = _login_user(client, phone="13800138233", nickname="ReviewGuardAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_strategy_for_review(app, strategy_id="pending-without-artifacts", owner_id=owner_id)

    response = client.patch(
        "/api/v1/admin/strategies/pending-without-artifacts/review",
        json={"status": "approved"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "STRATEGY_REVIEW_EVIDENCE_INCOMPLETE"


def test_admin_strategy_review_approve_updates_state_and_writes_side_effects(client, app, monkeypatch, tmp_path):
    admin_token, admin_id = _login_user(client, phone="13800138214", nickname="ApproveAdmin")
    _, owner_id = _login_user(client, phone="13800138215", nickname="ApproveAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        owner = db.session.get(User, owner_id)
        admin.role = "admin"
        owner.nickname = "审核作者"
        db.session.commit()

    _seed_strategy_for_review(
        app,
        strategy_id="pending-approve",
        owner_id=owner_id,
        title="Approve Me",
        updated_at=1700000000000,
        last_update=1700000000000,
    )
    _seed_review_artifacts(
        app,
        strategy_id="pending-approve",
        owner_id=owner_id,
        tmp_path=tmp_path,
        checksum=None,
    )

    delay_calls = []

    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    response = client.patch(
        "/api/v1/admin/strategies/pending-approve/review",
        json={"status": "approved"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"strategy_id": "pending-approve", "review_status": "approved"}

    with app.app_context():
        strategy = db.session.get(Strategy, "pending-approve")
        assert strategy.review_status == "approved"
        assert strategy.is_public is True
        assert strategy.updated_at > 1700000000000
        assert strategy.last_update == strategy.updated_at

        notification = Notification.query.filter_by(
            user_id=owner_id,
            type="strategy_review_result",
        ).first()
        assert notification is not None
        assert notification.title == "策略审核通过"
        assert "Approve Me" in (notification.content or "")
        assert "策略广场上架" in (notification.content or "")

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="strategy_approve",
            target_id="pending-approve",
        ).first()
        assert audit is not None
        assert audit.details == {
            "review_status_before": "pending",
            "review_status_after": "approved",
            "reason": None,
            "strategy_owner_id": owner_id,
            "admin_id": admin_id,
        }

    assert delay_calls == [
        {
            "user_id": owner_id,
            "event_type": "strategy_review_result",
            "context_data": {
                "strategy_name": "Approve Me",
                "status": "approved",
                "reason": None,
                "target_id": "pending-approve",
            },
        }
    ]


def test_admin_strategy_review_reject_requires_reason_and_marks_private(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138216", nickname="RejectAdmin")
    _, owner_id = _login_user(client, phone="13800138217", nickname="RejectAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_strategy_for_review(app, strategy_id="pending-reject", owner_id=owner_id, title="Reject Me")

    missing_reason = client.patch(
        "/api/v1/admin/strategies/pending-reject/review",
        json={"status": "rejected", "reason": "   "},
        headers=_auth_headers(admin_token),
    )

    assert missing_reason.status_code == 422
    assert missing_reason.json["error"]["code"] == "REVIEW_REASON_REQUIRED"

    delay_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    response = client.patch(
        "/api/v1/admin/strategies/pending-reject/review",
        json={"status": "rejected", "reason": "  风险披露不足  "},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"strategy_id": "pending-reject", "review_status": "rejected"}

    with app.app_context():
        strategy = db.session.get(Strategy, "pending-reject")
        assert strategy.review_status == "rejected"
        assert strategy.is_public is False

        notification = Notification.query.filter_by(
            user_id=owner_id,
            type="strategy_review_result",
        ).first()
        assert notification is not None
        assert notification.title == "策略审核被拒绝"
        assert "风险披露不足" in (notification.content or "")
        assert "未通过审核" in (notification.content or "")

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="strategy_reject",
            target_id="pending-reject",
        ).first()
        assert audit is not None
        assert audit.details["reason"] == "风险披露不足"

    assert delay_calls[0]["context_data"]["reason"] == "风险披露不足"


def test_admin_strategy_review_returns_404_for_missing_strategy(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138218", nickname="MissingAdmin")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    response = client.patch(
        "/api/v1/admin/strategies/not-found/review",
        json={"status": "approved"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "STRATEGY_NOT_FOUND"


def test_admin_strategy_review_returns_conflict_when_already_processed(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138219", nickname="ConflictAdmin")
    _, owner_id = _login_user(client, phone="13800138220", nickname="ConflictAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_strategy_for_review(
        app,
        strategy_id="already-approved",
        owner_id=owner_id,
        review_status="approved",
        is_public=True,
    )

    response = client.patch(
        "/api/v1/admin/strategies/already-approved/review",
        json={"status": "rejected", "reason": "late change"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "STRATEGY_REVIEW_CONFLICT"


def test_admin_strategy_review_rejects_invalid_status(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138221", nickname="InvalidStatusAdmin")
    _, owner_id = _login_user(client, phone="13800138222", nickname="InvalidStatusAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_strategy_for_review(app, strategy_id="pending-invalid", owner_id=owner_id)

    response = client.patch(
        "/api/v1/admin/strategies/pending-invalid/review",
        json={"status": "invalid_value"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "REVIEW_STATUS_INVALID"


def test_admin_report_queue_lists_pending_reports_for_admins(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138231", nickname="ReportAdmin")
    _, reporter_id = _login_user(client, phone="13800138232", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138233", nickname="ReportAuthor")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        reporter = db.session.get(User, reporter_id)
        owner = db.session.get(User, owner_id)
        admin.role = "admin"
        reporter.nickname = "SignalWatcher"
        owner.nickname = "AlphaBuilder"
        db.session.commit()

    _seed_public_strategy_for_reports(
        app,
        strategy_id="reported-alpha",
        owner_id=owner_id,
        title="Reported Alpha",
    )
    _seed_report(
        app,
        report_id="report-newer",
        reporter_id=reporter_id,
        strategy_id="reported-alpha",
        reason="The strategy includes unsupported guarantees in the description.",
        created_at=now_utc(),
    )
    _seed_report(
        app,
        report_id="report-dismissed",
        reporter_id=reporter_id,
        strategy_id="reported-alpha",
        reason="Already processed report.",
        status="dismissed",
        created_at=now_utc(),
    )

    response = client.get(
        "/api/v1/admin/reports?status=pending&page=1&per_page=20",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["meta"] == {"total": 1, "page": 1, "per_page": 20}
    assert response.json["data"][0]["id"] == "report-newer"
    assert response.json["data"][0]["reporter_nickname"] == "SignalWatcher"
    assert response.json["data"][0]["strategy_title"] == "Reported Alpha"
    assert response.json["data"][0]["strategy_author_nickname"] == "AlphaBuilder"
    assert response.json["data"][0]["reason"] == "The strategy includes unsupported guarantees in the description."
    assert response.json["data"][0]["status"] == "pending"


def test_admin_report_queue_rejects_non_admin_users(client, app):
    token, reporter_id = _login_user(client, phone="13800138234", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138235", nickname="Owner")
    _seed_public_strategy_for_reports(app, strategy_id="reported-forbidden", owner_id=owner_id)
    _seed_report(app, report_id="report-forbidden", reporter_id=reporter_id, strategy_id="reported-forbidden")

    response = client.get(
        "/api/v1/admin/reports?status=pending&page=1&per_page=20",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"


def test_admin_resolve_report_takedown_updates_strategy_and_side_effects(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138236", nickname="TakedownAdmin")
    _, reporter_id = _login_user(client, phone="13800138237", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138238", nickname="Owner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        owner = db.session.get(User, owner_id)
        admin.role = "admin"
        owner.email = "owner@example.com"
        db.session.commit()

    _seed_public_strategy_for_reports(
        app,
        strategy_id="reported-takedown",
        owner_id=owner_id,
        title="Take Me Down",
    )
    _seed_report(
        app,
        report_id="report-primary",
        reporter_id=reporter_id,
        strategy_id="reported-takedown",
        reason="This strategy uses prohibited marketing language.",
    )
    _seed_report(
        app,
        report_id="report-secondary",
        reporter_id=reporter_id,
        strategy_id="reported-takedown",
        reason="Second pending report should also be closed.",
    )

    delay_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    response = client.patch(
        "/api/v1/admin/reports/report-primary/resolve",
        json={"action": "takedown", "admin_note": "Repeated compliance violations"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"report_id": "report-primary", "status": "reviewed", "action": "takedown"}

    with app.app_context():
        strategy = db.session.get(Strategy, "reported-takedown")
        primary = db.session.get(Report, "report-primary")
        secondary = db.session.get(Report, "report-secondary")

        assert strategy.is_public is False
        assert primary.status == "reviewed"
        assert primary.reviewed_by == admin_id
        assert primary.admin_note == "Repeated compliance violations"
        assert secondary.status == "reviewed"
        assert secondary.reviewed_by == admin_id

        notification = Notification.query.filter_by(
            user_id=owner_id,
            type="strategy_takedown",
        ).first()
        assert notification is not None
        assert "Take Me Down" in (notification.content or "")
        assert "This strategy uses prohibited marketing language." in (notification.content or "")

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="strategy_takedown",
            target_id="reported-takedown",
        ).first()
        assert audit is not None
        assert audit.details["report_id"] == "report-primary"
        assert audit.details["strategy_owner_id"] == owner_id
        assert audit.details["admin_note"] == "Repeated compliance violations"

    assert delay_calls == [
        {
            "user_id": owner_id,
            "event_type": "strategy_takedown",
            "context_data": {
                "strategy_name": "Take Me Down",
                "reason": "This strategy uses prohibited marketing language.",
                "target_id": "reported-takedown",
            },
        }
    ]


def test_admin_resolve_report_dismiss_marks_report_only(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138239", nickname="DismissAdmin")
    _, reporter_id = _login_user(client, phone="13800138240", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138241", nickname="Owner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_public_strategy_for_reports(app, strategy_id="reported-dismiss", owner_id=owner_id, title="Dismiss Me")
    _seed_report(
        app,
        report_id="report-dismiss-target",
        reporter_id=reporter_id,
        strategy_id="reported-dismiss",
        reason="This report should be dismissed.",
    )

    delay_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    response = client.patch(
        "/api/v1/admin/reports/report-dismiss-target/resolve",
        json={"action": "dismiss", "admin_note": "Insufficient evidence"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"report_id": "report-dismiss-target", "status": "dismissed", "action": "dismiss"}

    with app.app_context():
        strategy = db.session.get(Strategy, "reported-dismiss")
        report = db.session.get(Report, "report-dismiss-target")

        assert strategy.is_public is True
        assert report.status == "dismissed"
        assert report.reviewed_by == admin_id
        assert report.admin_note == "Insufficient evidence"
        assert Notification.query.count() == 0

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="report_dismiss",
            target_id="report-dismiss-target",
        ).first()
        assert audit is not None
        assert audit.details["strategy_id"] == "reported-dismiss"
        assert audit.details["admin_note"] == "Insufficient evidence"

    assert delay_calls == []


def test_admin_resolve_report_rejects_duplicate_processing(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138242", nickname="ConflictAdmin")
    _, reporter_id = _login_user(client, phone="13800138243", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138244", nickname="Owner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_public_strategy_for_reports(app, strategy_id="reported-conflict", owner_id=owner_id)
    _seed_report(
        app,
        report_id="report-conflict",
        reporter_id=reporter_id,
        strategy_id="reported-conflict",
        status="dismissed",
    )

    response = client.patch(
        "/api/v1/admin/reports/report-conflict/resolve",
        json={"action": "dismiss"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "REPORT_RESOLUTION_CONFLICT"


def test_admin_backtest_queue_stats_returns_metrics_and_stuck_jobs(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138251", nickname="QueueAdmin")
    _, owner_id = _login_user(client, phone="13800138252", nickname="JobOwner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_public_strategy_for_reports(
        app,
        strategy_id="queue-strategy",
        owner_id=owner_id,
        title="Queue Strategy",
    )

    now = now_utc()
    _seed_backtest_job(
        app,
        job_id="job-pending",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.PENDING.value,
        created_at=now - timedelta(minutes=5),
    )
    _seed_backtest_job(
        app,
        job_id="job-running-fresh",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.RUNNING.value,
        started_at=now - timedelta(minutes=4),
        created_at=now - timedelta(minutes=6),
    )
    _seed_backtest_job(
        app,
        job_id="job-running-stuck",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.RUNNING.value,
        started_at=now - timedelta(minutes=15),
        created_at=now - timedelta(minutes=16),
    )
    _seed_backtest_job(
        app,
        job_id="job-completed-short",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.COMPLETED.value,
        started_at=now - timedelta(minutes=8),
        completed_at=now - timedelta(minutes=6),
        created_at=now - timedelta(minutes=9),
    )
    _seed_backtest_job(
        app,
        job_id="job-completed-long",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.COMPLETED.value,
        started_at=now - timedelta(minutes=12),
        completed_at=now - timedelta(minutes=7),
        created_at=now - timedelta(minutes=13),
    )
    _seed_backtest_job(
        app,
        job_id="job-failed",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.FAILED.value,
        completed_at=now - timedelta(minutes=20),
        created_at=now - timedelta(minutes=21),
        error_message="boom",
    )
    _seed_backtest_job(
        app,
        job_id="job-timeout",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.TIMEOUT.value,
        completed_at=now - timedelta(minutes=25),
        created_at=now - timedelta(minutes=26),
        error_message="soft_time_limit_exceeded",
    )
    _seed_backtest_job(
        app,
        job_id="job-failed-old",
        user_id=owner_id,
        strategy_id="queue-strategy",
        status=BacktestJobStatus.FAILED.value,
        completed_at=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2, minutes=5),
        error_message="old",
    )

    response = client.get(
        "/api/v1/admin/backtest/queue-stats",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"]["stats"] == {
        "pending": 1,
        "running": 2,
        "avg_duration": 210,
        "failure_rate_1h": 0.5,
    }
    assert [item["job_id"] for item in response.json["data"]["stuck_jobs"]] == ["job-running-stuck"]
    assert response.json["data"]["stuck_jobs"][0]["user_id"] == owner_id
    assert response.json["data"]["stuck_jobs"][0]["strategy_id"] == "queue-strategy"
    assert response.json["data"]["stuck_jobs"][0]["strategy_name"] == "Queue Strategy"
    assert response.json["data"]["stuck_jobs"][0]["running_duration_seconds"] >= 900
    assert response.json["data"]["stuck_jobs"][0]["started_at"] is not None


def test_admin_backtest_queue_stats_returns_zeroes_without_jobs(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138253", nickname="ZeroAdmin")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    response = client.get(
        "/api/v1/admin/backtest/queue-stats",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {
        "stats": {
            "pending": 0,
            "running": 0,
            "avg_duration": 0,
            "failure_rate_1h": 0,
        },
        "stuck_jobs": [],
    }


def test_admin_backtest_queue_stats_rejects_non_admin_users(client):
    token, _ = _login_user(client, phone="13800138254", nickname="PlainQueueUser")

    response = client.get(
        "/api/v1/admin/backtest/queue-stats",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"


def test_admin_terminate_backtest_job_updates_state_and_side_effects(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138255", nickname="TerminateAdmin")
    _, owner_id = _login_user(client, phone="13800138256", nickname="TerminateOwner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_public_strategy_for_reports(
        app,
        strategy_id="terminate-strategy",
        owner_id=owner_id,
        title="Terminate Strategy",
    )
    started_at = now_utc() - timedelta(minutes=14)
    _seed_backtest_job(
        app,
        job_id="running-job",
        user_id=owner_id,
        strategy_id="terminate-strategy",
        status=BacktestJobStatus.RUNNING.value,
        started_at=started_at,
        created_at=started_at - timedelta(minutes=1),
    )

    revoke_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.celery_app.control,
        "revoke",
        lambda *args, **kwargs: revoke_calls.append((args, kwargs)),
    )

    response = client.delete(
        "/api/v1/admin/backtest/running-job",
        json={"admin_note": "worker stuck"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"job_id": "running-job", "status": "terminated"}
    assert revoke_calls == [(("running-job",), {"terminate": True})]

    with app.app_context():
        job = db.session.get(BacktestJob, "running-job")
        assert job.status == BacktestJobStatus.FAILED.value
        assert job.error_message == "管理员手动终止"
        assert job.completed_at is not None

        notification = Notification.query.filter_by(
            user_id=owner_id,
            type="job_terminated",
        ).first()
        assert notification is not None
        assert notification.title == "回测任务已终止"
        assert "Terminate Strategy" in (notification.content or "")
        assert "worker stuck" in (notification.content or "")

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="job_terminate",
            target_id="running-job",
        ).first()
        assert audit is not None
        assert audit.target_type == "backtest_job"
        assert audit.details["user_id"] == owner_id
        assert audit.details["strategy_id"] == "terminate-strategy"
        assert audit.details["admin_note"] == "worker stuck"
        assert audit.details["running_duration_seconds"] >= 840


def test_admin_terminate_pending_backtest_job_succeeds(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138257", nickname="PendingTerminateAdmin")
    _, owner_id = _login_user(client, phone="13800138258", nickname="PendingTerminateOwner")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    _seed_backtest_job(
        app,
        job_id="pending-job",
        user_id=owner_id,
        status=BacktestJobStatus.PENDING.value,
    )

    revoke_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.celery_app.control,
        "revoke",
        lambda *args, **kwargs: revoke_calls.append((args, kwargs)),
    )

    response = client.delete(
        "/api/v1/admin/backtest/pending-job",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert revoke_calls == [(("pending-job",), {"terminate": True})]

    with app.app_context():
        job = db.session.get(BacktestJob, "pending-job")
        assert job.status == BacktestJobStatus.FAILED.value
        assert job.completed_at is not None


def test_admin_terminate_backtest_job_returns_conflict_for_completed_jobs(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138259", nickname="CompletedAdmin")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    now = now_utc()
    _seed_backtest_job(
        app,
        job_id="completed-job",
        status=BacktestJobStatus.COMPLETED.value,
        started_at=now - timedelta(minutes=3),
        completed_at=now - timedelta(minutes=1),
    )

    response = client.delete(
        "/api/v1/admin/backtest/completed-job",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "JOB_TERMINATION_CONFLICT"


def test_admin_terminate_backtest_job_returns_404_for_missing_job(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138260", nickname="MissingJobAdmin")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    response = client.delete(
        "/api/v1/admin/backtest/missing-job",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "JOB_NOT_FOUND"


def test_admin_terminate_backtest_job_rejects_non_admin_users(client, app):
    token, user_id = _login_user(client, phone="13800138261", nickname="PlainTerminateUser")
    _seed_backtest_job(
        app,
        job_id="forbidden-job",
        user_id=user_id,
        status=BacktestJobStatus.RUNNING.value,
        started_at=now_utc() - timedelta(minutes=11),
    )

    response = client.delete(
        "/api/v1/admin/backtest/forbidden-job",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"


def test_admin_users_list_returns_masked_users_with_pagination(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138241", nickname="UserAdmin")
    _, newer_user_id = _login_user(client, phone="13800138242", nickname="Recent User")
    _, older_user_id = _login_user(client, phone="13800138243", nickname="Older User")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"

        newer_user = db.session.get(User, newer_user_id)
        newer_user.nickname = "Recent User"
        newer_user.plan_level = "pro"
        newer_user.created_at = datetime(2026, 3, 26, 4, 30, tzinfo=timezone.utc)
        newer_user.is_banned = True

        older_user = db.session.get(User, older_user_id)
        older_user.nickname = "Older User"
        older_user.plan_level = "starter"
        older_user.created_at = datetime(2026, 3, 25, 2, 0, tzinfo=timezone.utc)
        db.session.commit()

    response = client.get(
        "/api/v1/admin/users?page=1&per_page=2",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["meta"] == {"total": 2, "page": 1, "per_page": 2}
    assert [item["user_id"] for item in response.json["data"]] == [newer_user_id, older_user_id]
    assert response.json["data"][0] == {
        "user_id": newer_user_id,
        "nickname": "Recent User",
        "phone": "138****8242",
        "created_at": "2026-03-26T12:30:00+08:00",
        "plan_level": "pro",
        "is_banned": True,
    }


def test_admin_users_list_supports_search_by_phone_or_nickname(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138244", nickname="SearchAdmin")
    _, alpha_user_id = _login_user(client, phone="13800138245", nickname="Alpha Quant")
    _, beta_user_id = _login_user(client, phone="13900138246", nickname="Beta Trader")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.get(User, alpha_user_id).nickname = "Alpha Quant"
        db.session.get(User, beta_user_id).nickname = "Beta Trader"
        db.session.commit()

    by_nickname = client.get(
        "/api/v1/admin/users?search=Alpha",
        headers=_auth_headers(admin_token),
    )
    by_phone = client.get(
        "/api/v1/admin/users?search=1390013",
        headers=_auth_headers(admin_token),
    )

    assert by_nickname.status_code == 200
    assert [item["user_id"] for item in by_nickname.json["data"]] == [alpha_user_id]
    assert by_phone.status_code == 200
    assert [item["user_id"] for item in by_phone.json["data"]] == [beta_user_id]


def test_admin_users_list_rejects_non_admin_users(client):
    token, _ = _login_user(client, phone="13800138247", nickname="PlainMember")

    response = client.get("/api/v1/admin/users", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"


def test_admin_user_ban_revokes_all_refresh_tokens_and_writes_side_effects(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138248", nickname="BanAdmin")
    _, target_user_id = _login_user(client, phone="13800138249", nickname="Risk User")
    second_device = client.application.test_client()
    _seed_code(second_device.application, "13800138249")
    second_login = second_device.post(
        "/api/v1/auth/login",
        json={"phone": "13800138249", "code": "123456"},
    )
    assert second_login.status_code == 200

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        db.session.commit()

    delay_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    response = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"is_banned": True, "ban_reason": "spam"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"user_id": target_user_id, "is_banned": True}

    from app.utils.redis_client import get_auth_store

    with app.app_context():
        banned_user = db.session.get(User, target_user_id)
        assert banned_user.is_banned is True

        token_rows = list(
            RefreshToken.query.filter_by(user_id=target_user_id).order_by(RefreshToken.created_at.asc()).all()
        )
        assert len(token_rows) == 2
        assert all(row.revoked_at is not None for row in token_rows)
        assert all(get_auth_store().is_token_blacklisted(row.jti) for row in token_rows)

        notification = (
            Notification.query.filter_by(user_id=target_user_id)
            .order_by(Notification.created_at.desc())
            .first()
        )
        assert notification is not None
        assert notification.type == "user_ban_status"
        assert "封禁" in notification.title

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="user_ban",
            target_type="user",
            target_id=target_user_id,
        ).first()
        assert audit is not None
        assert audit.details["ban_reason"] == "spam"
        assert audit.details["token_revoked_count"] == 2

    assert delay_calls == [
        {
            "user_id": target_user_id,
            "event_type": "user_ban_status",
            "context_data": {
                "is_banned": True,
                "ban_reason": "spam",
                "target_id": target_user_id,
            },
        }
    ]


def test_admin_user_ban_is_idempotent_for_same_state(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138250", nickname="IdempotentAdmin")
    _, target_user_id = _login_user(client, phone="13800138251", nickname="Already Banned")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        target_user = db.session.get(User, target_user_id)
        target_user.is_banned = True
        db.session.commit()

    first = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"is_banned": True, "ban_reason": "repeat"},
        headers=_auth_headers(admin_token),
    )
    second = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"is_banned": True, "ban_reason": "repeat"},
        headers=_auth_headers(admin_token),
    )

    assert first.status_code == 200
    assert second.status_code == 200

    with app.app_context():
        assert AuditLog.query.filter_by(action="user_ban", target_id=target_user_id).count() == 0
        assert Notification.query.filter_by(user_id=target_user_id, type="user_ban_status").count() == 0


def test_admin_user_unban_updates_state_and_writes_audit(client, app, monkeypatch):
    admin_token, admin_id = _login_user(client, phone="13800138252", nickname="UnbanAdmin")
    _, target_user_id = _login_user(client, phone="13800138253", nickname="Recovered User")

    delay_calls = []
    from app.blueprints import admin as admin_blueprint

    monkeypatch.setattr(
        admin_blueprint.send_email_notification,
        "delay",
        lambda **kwargs: delay_calls.append(kwargs),
    )

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        target_user = db.session.get(User, target_user_id)
        target_user.is_banned = True
        db.session.commit()

    response = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"is_banned": False},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"user_id": target_user_id, "is_banned": False}

    with app.app_context():
        target_user = db.session.get(User, target_user_id)
        assert target_user.is_banned is False

        audit = AuditLog.query.filter_by(
            operator_id=admin_id,
            action="user_unban",
            target_type="user",
            target_id=target_user_id,
        ).first()
        assert audit is not None

        notification = (
            Notification.query.filter_by(user_id=target_user_id)
            .order_by(Notification.created_at.desc())
            .first()
        )
        assert notification is not None
        assert notification.type == "user_ban_status"
        assert "解封" in notification.title

    assert delay_calls == [
        {
            "user_id": target_user_id,
            "event_type": "user_ban_status",
            "context_data": {
                "is_banned": False,
                "ban_reason": None,
                "target_id": target_user_id,
            },
        }
    ]


def test_admin_audit_logs_list_supports_filters_and_pagination(client, app):
    admin_token, admin_id = _login_user(client, phone="13800138254", nickname="AuditAdmin")
    _, operator_id = _login_user(client, phone="13800138255", nickname="Operator User")

    with app.app_context():
        admin = db.session.get(User, admin_id)
        admin.role = "admin"
        operator = db.session.get(User, operator_id)
        operator.nickname = "Operator User"
        db.session.add(
            AuditLog(
                id="audit-log-1",
                operator_id=operator_id,
                action="user_ban",
                target_type="user",
                target_id="user-100",
                details={"ban_reason": "spam"},
                created_at=datetime(2026, 3, 26, 1, 0, tzinfo=timezone.utc),
            )
        )
        db.session.add(
            AuditLog(
                id="audit-log-2",
                operator_id=admin_id,
                action="report_dismiss",
                target_type="report",
                target_id="report-200",
                details={"admin_note": "not valid"},
                created_at=datetime(2026, 3, 25, 1, 0, tzinfo=timezone.utc),
            )
        )
        db.session.commit()

    response = client.get(
        f"/api/v1/admin/audit-logs?operator_id={operator_id}&action=user_ban&target_type=user&target_id=user-100&page=1&per_page=1",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json["meta"] == {"total": 1, "page": 1, "per_page": 1}
    assert response.json["data"] == [
        {
            "id": "audit-log-1",
            "operator_id": operator_id,
            "operator_nickname": "Operator User",
            "action": "user_ban",
            "target_type": "user",
            "target_id": "user-100",
            "details": {"ban_reason": "spam"},
            "created_at": "2026-03-26T09:00:00+08:00",
        }
    ]


def test_admin_audit_logs_rejects_non_admin_users(client, app):
    token, operator_id = _login_user(client, phone="13800138256", nickname="AuditReader")

    with app.app_context():
        db.session.add(
            AuditLog(
                id="audit-log-forbidden",
                operator_id=operator_id,
                action="user_ban",
                target_type="user",
                target_id="user-1",
            )
        )
        db.session.commit()

    response = client.get("/api/v1/admin/audit-logs", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json["error"]["code"] == "FORBIDDEN"
