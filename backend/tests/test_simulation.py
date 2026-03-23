from decimal import Decimal

from app.extensions import db
from app.models import SimulationBot, SimulationPosition, SimulationRecord, Strategy, User


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


# ── Story 7.3: GET /bots ──────────────────────────────────────────────────────


def test_list_bots_returns_empty_for_new_user(client):
    token, _ = _login_user(client, phone="13800138200", nickname="EmptyUser")
    response = client.get("/api/v1/simulation/bots", headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json["data"] == []


def test_list_bots_returns_user_bots(client, app):
    token, user_id = _login_user(client, phone="13800138201", nickname="ListUser")

    with app.app_context():
        _create_strategy("list-strategy", user_id)
        db.session.flush()
        db.session.add(
            SimulationBot(
                user_id=user_id,
                strategy_id="list-strategy",
                initial_capital=Decimal("50000"),
                status="active",
            )
        )
        db.session.commit()

    response = client.get("/api/v1/simulation/bots", headers=_auth_headers(token))
    assert response.status_code == 200
    data = response.json["data"]
    assert len(data) == 1
    bot = data[0]
    assert bot["strategy_id"] == "list-strategy"
    assert bot["strategy_name"] == "Strategy list-strategy"
    assert bot["initial_capital"] == "50000.00"
    assert bot["status"] == "active"
    assert bot["created_at"].endswith("+08:00")


def test_list_bots_unauthenticated(client):
    response = client.get("/api/v1/simulation/bots")
    assert response.status_code == 401


def test_list_bots_only_current_user(client, app):
    token_a, user_a = _login_user(client, phone="13800138202", nickname="UserA")
    token_b, user_b = _login_user(client, phone="13800138203", nickname="UserB")

    with app.app_context():
        _create_strategy("strategy-a", user_a)
        db.session.flush()
        db.session.add(
            SimulationBot(
                user_id=user_a,
                strategy_id="strategy-a",
                initial_capital=Decimal("100000"),
                status="active",
            )
        )
        db.session.commit()

    response = client.get("/api/v1/simulation/bots", headers=_auth_headers(token_b))
    assert response.status_code == 200
    assert response.json["data"] == []


def test_list_bots_deleted_strategy_shows_placeholder(client, app):
    token, user_id = _login_user(client, phone="13800138204", nickname="DeletedStrat")

    with app.app_context():
        db.session.add(
            SimulationBot(
                user_id=user_id,
                strategy_id="nonexistent-strategy",
                initial_capital=Decimal("10000"),
                status="active",
            )
        )
        db.session.commit()

    response = client.get("/api/v1/simulation/bots", headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json["data"][0]["strategy_name"] == "(策略已删除)"


# ── Story 7.3: GET /bots/:id/positions ───────────────────────────────────────


def _create_bot(app, user_id, strategy_id, capital=100000):
    with app.app_context():
        bot = SimulationBot(
            user_id=user_id,
            strategy_id=strategy_id,
            initial_capital=Decimal(str(capital)),
            status="active",
        )
        db.session.add(bot)
        db.session.commit()
        return bot.id


def _create_record(app, bot_id, *, trade_date="2026-03-20", equity="105000.00", cash="55000.00", daily_return="0.000500"):
    from datetime import date as date_cls

    with app.app_context():
        record = SimulationRecord(
            bot_id=bot_id,
            trade_date=date_cls.fromisoformat(trade_date),
            equity=Decimal(equity),
            cash=Decimal(cash),
            daily_return=Decimal(daily_return),
        )
        db.session.add(record)
        db.session.commit()


def _create_trade(app, bot_id, *, trade_date="2026-03-20", symbol="000001.XSHG", side="buy", price="15.2300", quantity="1000.0000"):
    from datetime import date as date_cls
    from app.models import SimulationTrade

    with app.app_context():
        trade = SimulationTrade(
            bot_id=bot_id,
            trade_date=date_cls.fromisoformat(trade_date),
            symbol=symbol,
            side=side,
            price=Decimal(price),
            quantity=Decimal(quantity),
        )
        db.session.add(trade)
        db.session.commit()


def test_get_positions_empty(client, app):
    token, user_id = _login_user(client, phone="13800138205", nickname="PosEmpty")

    with app.app_context():
        _create_strategy("pos-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "pos-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/positions",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json["data"] == []


def test_get_positions_returns_positions(client, app):
    token, user_id = _login_user(client, phone="13800138206", nickname="PosUser")

    with app.app_context():
        _create_strategy("pos-strategy-2", user_id)
        db.session.flush()
        bot = SimulationBot(
            user_id=user_id,
            strategy_id="pos-strategy-2",
            initial_capital=Decimal("100000"),
            status="active",
        )
        db.session.add(bot)
        db.session.flush()
        db.session.add(
            SimulationPosition(
                bot_id=bot.id,
                symbol="000001.XSHG",
                quantity=Decimal("1000.0000"),
                avg_cost=Decimal("52.0000"),
            )
        )
        db.session.commit()
        bot_id = bot.id

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/positions",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json["data"]
    assert len(data) == 1
    pos = data[0]
    assert pos["symbol"] == "000001.XSHG"
    assert pos["quantity"] == "1000.0000"
    assert pos["avg_cost"] == "52.0000"
    assert pos["updated_at"].endswith("+08:00")


def test_get_positions_bot_not_found(client):
    token, _ = _login_user(client, phone="13800138207", nickname="NotFoundUser")
    response = client.get(
        "/api/v1/simulation/bots/nonexistent-bot-id/positions",
        headers=_auth_headers(token),
    )
    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_positions_other_user_bot(client, app):
    token_a, user_a = _login_user(client, phone="13800138208", nickname="OwnerA")
    token_b, user_b = _login_user(client, phone="13800138209", nickname="AttackerB")

    with app.app_context():
        _create_strategy("owner-strategy", user_a)
        db.session.commit()

    bot_id = _create_bot(app, user_a, "owner-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/positions",
        headers=_auth_headers(token_b),
    )
    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_positions_unauthenticated(client):
    response = client.get("/api/v1/simulation/bots/any-bot-id/positions")
    assert response.status_code == 401


# SSE endpoint is intentionally not unit-tested here because the long-lived
# connection shape is better covered with higher-level integration testing.


def test_get_records_empty(client, app):
    token, user_id = _login_user(client, phone="13800138210", nickname="RecordEmpty")

    with app.app_context():
        _create_strategy("record-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "record-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/records",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == []


def test_get_records_returns_data(client, app):
    token, user_id = _login_user(client, phone="13800138211", nickname="RecordUser")

    with app.app_context():
        _create_strategy("record-strategy-2", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "record-strategy-2")
    _create_record(app, bot_id)

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/records",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == [
        {
            "trade_date": "2026-03-20",
            "equity": "105000.00",
            "cash": "55000.00",
            "daily_return": "0.000500",
        }
    ]


def test_get_records_bot_not_found(client):
    token, _ = _login_user(client, phone="13800138212", nickname="RecordNotFound")

    response = client.get(
        "/api/v1/simulation/bots/nonexistent-bot-id/records",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_records_other_user_bot(client, app):
    token_a, user_a = _login_user(client, phone="13800138213", nickname="RecordOwner")
    token_b, _ = _login_user(client, phone="13800138214", nickname="RecordIntruder")

    with app.app_context():
        _create_strategy("record-owner-strategy", user_a)
        db.session.commit()

    bot_id = _create_bot(app, user_a, "record-owner-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/records",
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_records_unauthenticated(client):
    response = client.get("/api/v1/simulation/bots/any-bot-id/records")

    assert response.status_code == 401


def test_get_trades_empty(client, app):
    token, user_id = _login_user(client, phone="13800138215", nickname="TradeEmpty")

    with app.app_context():
        _create_strategy("trade-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "trade-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/trades",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == []


def test_get_trades_returns_data(client, app):
    token, user_id = _login_user(client, phone="13800138216", nickname="TradeUser")

    with app.app_context():
        _create_strategy("trade-strategy-2", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "trade-strategy-2")
    _create_trade(app, bot_id)

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/trades",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == [
        {
            "trade_date": "2026-03-20",
            "symbol": "000001.XSHG",
            "side": "buy",
            "price": "15.2300",
            "quantity": "1000.0000",
        }
    ]


def test_get_trades_bot_not_found(client):
    token, _ = _login_user(client, phone="13800138217", nickname="TradeNotFound")

    response = client.get(
        "/api/v1/simulation/bots/nonexistent-bot-id/trades",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_trades_other_user_bot(client, app):
    token_a, user_a = _login_user(client, phone="13800138218", nickname="TradeOwner")
    token_b, _ = _login_user(client, phone="13800138219", nickname="TradeIntruder")

    with app.app_context():
        _create_strategy("trade-owner-strategy", user_a)
        db.session.commit()

    bot_id = _create_bot(app, user_a, "trade-owner-strategy")

    response = client.get(
        f"/api/v1/simulation/bots/{bot_id}/trades",
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_get_trades_unauthenticated(client):
    response = client.get("/api/v1/simulation/bots/any-bot-id/trades")

    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────


def test_users_me_includes_sim_disclaimer_accepted_flag(client, app):
    token, user_id = _login_user(client, phone="13800138105", nickname="MeUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.sim_disclaimer_accepted = True
        db.session.commit()

    response = client.get("/api/v1/users/me", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json["data"]["sim_disclaimer_accepted"] is True


# ── Story 7.5: PATCH /bots/:id ────────────────────────────────────────────


def test_patch_bot_pauses_active_bot(client, app):
    token, user_id = _login_user(client, phone="13800138300", nickname="Pauser")

    with app.app_context():
        _create_strategy("patch-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "patch-strategy")

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
        json={"status": "paused"},
    )

    assert response.status_code == 200
    data = response.json["data"]
    assert data["id"] == bot_id
    assert data["status"] == "paused"

    with app.app_context():
        bot = db.session.get(SimulationBot, bot_id)
        assert bot.status == "paused"


def test_patch_bot_resumes_paused_bot(client, app):
    token, user_id = _login_user(client, phone="13800138301", nickname="Resumer")

    with app.app_context():
        _create_strategy("resume-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "resume-strategy")

    with app.app_context():
        bot = db.session.get(SimulationBot, bot_id)
        bot.status = "paused"
        db.session.commit()

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
        json={"status": "active"},
    )

    assert response.status_code == 200
    assert response.json["data"]["status"] == "active"


def test_patch_bot_returns_422_for_invalid_status(client, app):
    token, user_id = _login_user(client, phone="13800138302", nickname="InvalidStatus")

    with app.app_context():
        _create_strategy("invalid-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "invalid-strategy")

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
        json={"status": "stopped"},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "VALIDATION_ERROR"


def test_patch_bot_returns_404_for_other_user_bot(client, app):
    token_a, user_a = _login_user(client, phone="13800138303", nickname="OwnerA")
    token_b, _ = _login_user(client, phone="13800138304", nickname="OwnerB")

    with app.app_context():
        _create_strategy("owned-by-a", user_a)
        db.session.commit()

    bot_id = _create_bot(app, user_a, "owned-by-a")

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token_b),
        json={"status": "paused"},
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_patch_bot_requires_auth(client, app):
    token, user_id = _login_user(client, phone="13800138305", nickname="NeedAuth")

    with app.app_context():
        _create_strategy("auth-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "auth-strategy")

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        json={"status": "paused"},
    )

    assert response.status_code == 401


# ── Story 7.5: DELETE /bots/:id ───────────────────────────────────────────


def test_delete_bot_soft_deletes_and_hides_from_list(client, app):
    token, user_id = _login_user(client, phone="13800138306", nickname="Deleter")

    with app.app_context():
        _create_strategy("delete-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "delete-strategy")

    response = client.delete(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json["data"] == {"deleted": True}

    with app.app_context():
        bot = db.session.get(SimulationBot, bot_id)
        assert bot.deleted_at is not None

    list_resp = client.get("/api/v1/simulation/bots", headers=_auth_headers(token))
    assert response.status_code == 200
    bot_ids = [b["id"] for b in list_resp.json["data"]]
    assert bot_id not in bot_ids


def test_delete_bot_preserves_simulation_records(client, app):
    token, user_id = _login_user(client, phone="13800138307", nickname="RecordKeeper")

    with app.app_context():
        _create_strategy("record-keep-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "record-keep-strategy")
    _create_record(app, bot_id)

    client.delete(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
    )

    with app.app_context():
        records = SimulationRecord.query.filter_by(bot_id=bot_id).all()
        assert len(records) == 1


def test_delete_bot_releases_slot_for_new_bot(client, app):
    token, user_id = _login_user(client, phone="13800138308", nickname="SlotUser")

    with app.app_context():
        user = db.session.get(User, user_id)
        user.plan_level = "free"
        _create_strategy("slot-strategy-1", user_id)
        _create_strategy("slot-strategy-2", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "slot-strategy-1")

    blocked = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={"strategy_id": "slot-strategy-2", "initial_capital": 100000},
    )
    assert blocked.status_code == 403

    client.delete(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
    )

    allowed = client.post(
        "/api/v1/simulation/bots",
        headers=_auth_headers(token),
        json={"strategy_id": "slot-strategy-2", "initial_capital": 100000},
    )
    assert allowed.status_code == 201


def test_delete_bot_returns_404_for_already_deleted(client, app):
    token, user_id = _login_user(client, phone="13800138309", nickname="DoubleDeleter")

    with app.app_context():
        _create_strategy("dd-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "dd-strategy")

    client.delete(f"/api/v1/simulation/bots/{bot_id}", headers=_auth_headers(token))

    response = client.delete(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_delete_bot_returns_404_for_other_user(client, app):
    token_a, user_a = _login_user(client, phone="13800138310", nickname="BotOwnerA")
    token_b, _ = _login_user(client, phone="13800138311", nickname="BotOwnerB")

    with app.app_context():
        _create_strategy("del-by-a", user_a)
        db.session.commit()

    bot_id = _create_bot(app, user_a, "del-by-a")

    response = client.delete(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"


def test_delete_bot_requires_auth(client, app):
    token, user_id = _login_user(client, phone="13800138312", nickname="NeedAuthDel")

    with app.app_context():
        _create_strategy("needauth-del-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "needauth-del-strategy")

    response = client.delete(f"/api/v1/simulation/bots/{bot_id}")

    assert response.status_code == 401


def test_patch_deleted_bot_returns_404(client, app):
    token, user_id = _login_user(client, phone="13800138313", nickname="PatchDeleted")

    with app.app_context():
        _create_strategy("pd-strategy", user_id)
        db.session.commit()

    bot_id = _create_bot(app, user_id, "pd-strategy")

    client.delete(f"/api/v1/simulation/bots/{bot_id}", headers=_auth_headers(token))

    response = client.patch(
        f"/api/v1/simulation/bots/{bot_id}",
        headers=_auth_headers(token),
        json={"status": "paused"},
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "BOT_NOT_FOUND"
