from app.extensions import db
from app.models import AuditLog, User


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
