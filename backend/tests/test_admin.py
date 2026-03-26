from app.extensions import db
from app.models import AuditLog, Notification, Report, Strategy, User
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


def test_admin_strategy_review_approve_updates_state_and_writes_side_effects(client, app, monkeypatch):
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
