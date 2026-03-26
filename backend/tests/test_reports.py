from datetime import timedelta

import pytest

from app.extensions import db
from app.models import Report, Strategy, User
from app.utils.time import now_ms, now_utc


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


def _seed_public_strategy(app, *, strategy_id, owner_id, title="Reported Strategy"):
    with app.app_context():
        strategy = Strategy(
            id=strategy_id,
            owner_id=owner_id,
            name=title,
            title=title,
            symbol="BTCUSDT",
            status="running",
            description="Public strategy eligible for reporting.",
            category="trend-following",
            tags=["trend"],
            display_metrics={"sharpe_ratio": 1.2, "max_drawdown": -9.5, "total_return": 20.1},
            review_status="approved",
            is_public=True,
            created_at=now_ms(),
            updated_at=now_ms(),
            last_update=now_ms(),
        )
        db.session.add(strategy)
        db.session.commit()


def test_submit_report_creates_pending_report_and_returns_201(client, app):
    reporter_token, reporter_id = _login_user(client, phone="13800138301", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138302", nickname="StrategyOwner")
    _seed_public_strategy(app, strategy_id="reported-strategy", owner_id=owner_id, title="Alpha Strategy")

    response = client.post(
        "/api/v1/marketplace/strategies/reported-strategy/report",
        json={"reason": "This strategy description contains misleading performance claims."},
        headers=_auth_headers(reporter_token),
    )

    assert response.status_code == 201
    assert response.json["data"]["report_id"]

    with app.app_context():
        report = db.session.get(Report, response.json["data"]["report_id"])
        assert report is not None
        assert report.reporter_id == reporter_id
        assert report.strategy_id == "reported-strategy"
        assert report.status == "pending"
        assert report.reason == "This strategy description contains misleading performance claims."
        assert report.reviewed_at is None
        assert report.reviewed_by is None


def test_submit_report_requires_auth(client, app):
    _, owner_id = _login_user(client, phone="13800138303", nickname="StrategyOwner")
    _seed_public_strategy(app, strategy_id="auth-required-strategy", owner_id=owner_id)

    response = client.post(
        "/api/v1/marketplace/strategies/auth-required-strategy/report",
        json={"reason": "This report should not be accepted without login."},
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_submit_report_rejects_self_report(client, app):
    owner_token, owner_id = _login_user(client, phone="13800138304", nickname="Owner")
    _seed_public_strategy(app, strategy_id="self-owned-strategy", owner_id=owner_id)

    response = client.post(
        "/api/v1/marketplace/strategies/self-owned-strategy/report",
        json={"reason": "Trying to report my own strategy should fail."},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "CANNOT_REPORT_OWN_STRATEGY"


def test_submit_report_rejects_duplicate_within_24_hours(client, app):
    reporter_token, reporter_id = _login_user(client, phone="13800138305", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138306", nickname="Owner")
    _seed_public_strategy(app, strategy_id="duplicate-window-strategy", owner_id=owner_id)

    with app.app_context():
        db.session.add(
            Report(
                reporter_id=reporter_id,
                strategy_id="duplicate-window-strategy",
                reason="Existing pending report within the duplicate window.",
                status="pending",
                created_at=now_utc() - timedelta(hours=12),
            )
        )
        db.session.commit()

    response = client.post(
        "/api/v1/marketplace/strategies/duplicate-window-strategy/report",
        json={"reason": "A second report inside 24 hours should conflict."},
        headers=_auth_headers(reporter_token),
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "REPORT_ALREADY_SUBMITTED"


def test_submit_report_requires_public_strategy(client, app):
    reporter_token, _ = _login_user(client, phone="13800138307", nickname="Reporter")

    response = client.post(
        "/api/v1/marketplace/strategies/missing-strategy/report",
        json={"reason": "Missing strategies should not be reportable."},
        headers=_auth_headers(reporter_token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "STRATEGY_NOT_FOUND"


@pytest.mark.parametrize(
    ("reason", "expected_code"),
    [
        ("   ", "REPORT_REASON_REQUIRED"),
        ("too short", "REPORT_REASON_INVALID"),
        ("x" * 501, "REPORT_REASON_INVALID"),
    ],
)
def test_submit_report_validates_reason_length(client, app, reason, expected_code):
    reporter_token, _ = _login_user(client, phone="13800138308", nickname="Reporter")
    _, owner_id = _login_user(client, phone="13800138309", nickname="Owner")
    _seed_public_strategy(app, strategy_id="validation-strategy", owner_id=owner_id)

    response = client.post(
        "/api/v1/marketplace/strategies/validation-strategy/report",
        json={"reason": reason},
        headers=_auth_headers(reporter_token),
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == expected_code
