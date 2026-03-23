from decimal import Decimal

from app.extensions import db
from app.models import SimulationBot, Strategy, User


def _seed_code(app, phone, code="123456", ttl=300):
    from app.utils.redis_client import get_auth_store

    with app.app_context():
        get_auth_store().set_verification_code(phone, code, ttl=ttl)


def _login_user(client, phone="13800138000", nickname="Trader"):
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


def _create_strategy(strategy_id, owner_id):
    strategy = Strategy(
        id=strategy_id,
        name=f"Strategy {strategy_id}",
        title=f"Strategy {strategy_id}",
        symbol="000001.XSHG",
        status="draft",
        owner_id=owner_id,
        returns=0,
        win_rate=0,
        max_drawdown=0,
        tags=[],
        trades=0,
    )
    db.session.add(strategy)
    return strategy


def test_accept_disclaimer_sets_flag_and_is_idempotent(client, app):
    token, user_id = _login_user(client, phone="13800138100", nickname="DisclaimerUser")

    first = client.post("/api/v1/simulation/disclaimer/accept", headers=_auth_headers(token))
    assert first.status_code == 200
    assert first.json["data"] == {"sim_disclaimer_accepted": True}

    second = client.post("/api/v1/simulation/disclaimer/accept", headers=_auth_headers(token))
    assert second.status_code == 200
    assert second.json["data"] == {"sim_disclaimer_accepted": True}

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.sim_disclaimer_accepted is True


def test_accept_disclaimer_requires_auth(client):
    response = client.post("/api/v1/simulation/disclaimer/accept")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"


def test_create_bot_persists_active_simulation_bot(client, app):
    token, user_id = _login_user(client, phone="13800138101", nickname="BotOwner")

    with app.app_context():
        _create_strategy("owned-strategy", user_id)
        db.session.commit()

    response = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={
            "strategy_id": "owned-strategy",
            "initial_capital": 100000,
        },
    )

    assert response.status_code == 201
    data = response.json["data"]
    assert data["strategy_id"] == "owned-strategy"
    assert data["initial_capital"] == "100000.00"
    assert data["status"] == "active"
    assert data["created_at"].endswith("+08:00")

    with app.app_context():
        bot = db.session.get(SimulationBot, data["id"])
        assert bot is not None
        assert bot.user_id == user_id
        assert bot.strategy_id == "owned-strategy"
        assert bot.initial_capital == Decimal("100000")
        assert bot.status == "active"


def test_create_bot_returns_404_when_strategy_is_not_owned_by_user(client, app):
    token, _ = _login_user(client, phone="13800138102", nickname="Caller")
    _, other_user_id = _login_user(client, phone="13800138103", nickname="Owner")

    with app.app_context():
        _create_strategy("foreign-strategy", other_user_id)
        db.session.commit()

    response = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={
            "strategy_id": "foreign-strategy",
            "initial_capital": 100000,
        },
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "STRATEGY_NOT_FOUND"


def test_create_bot_enforces_plan_slot_limit_and_ignores_paused_bots(client, app):
    token, user_id = _login_user(client, phone="13800138104", nickname="Limited")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "free"
        _create_strategy("strategy-one", user_id)
        _create_strategy("strategy-two", user_id)
        db.session.flush()
        db.session.add(
            SimulationBot(
                user_id=user_id,
                strategy_id="strategy-one",
                initial_capital=Decimal("100000"),
                status="active",
            )
        )
        db.session.commit()

    limited = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={
            "strategy_id": "strategy-two",
            "initial_capital": 100000,
        },
    )

    assert limited.status_code == 403
    assert limited.json["error"]["code"] == "SIMULATION_SLOT_LIMIT_REACHED"

    with app.app_context():
        active_bot = SimulationBot.query.filter_by(user_id=user_id, status="active").one()
        active_bot.status = "paused"
        db.session.commit()

    allowed = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={
            "strategy_id": "strategy-two",
            "initial_capital": 100000,
        },
    )

    assert allowed.status_code == 201
    assert allowed.json["data"]["status"] == "active"


def test_users_me_includes_sim_disclaimer_accepted_flag(client, app):
    token, user_id = _login_user(client, phone="13800138105", nickname="MeUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.sim_disclaimer_accepted = True
        db.session.commit()

    response = client.get("/api/v1/users/me", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"]["sim_disclaimer_accepted"] is True
