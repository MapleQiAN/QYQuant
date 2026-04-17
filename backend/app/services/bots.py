from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from ..extensions import db
from ..models import BotEquitySnapshot, BotInstance, IntegrationProvider, Order, Strategy, User, UserIntegration
from ..quota import get_bot_slot_limit
from ..utils.time import format_beijing_iso_ms, now_ms
from . import integrations as integrations_service

ACTIVE_BOT_STATUSES = {"active"}
ALLOWED_STATUSES = {"active", "paused"}
MIN_BOT_CAPITAL = Decimal("1000")
BALANCE_KEYS = ("available_cash", "available", "withdrawable_cash", "buying_power", "cash")


@dataclass(slots=True)
class BotServiceError(Exception):
    code: str
    message: str
    status: int

    def __str__(self) -> str:
        return self.message


def _as_decimal(value, *, default: Decimal | None = None) -> Decimal:
    if value is None:
        if default is None:
            raise InvalidOperation("missing decimal value")
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        if default is not None:
            return default
        raise exc


def _format_runtime(created_at_ms: int | None) -> str:
    if not created_at_ms:
        return "0h"

    elapsed_ms = max(0, now_ms() - int(created_at_ms))
    total_hours = elapsed_ms // (1000 * 60 * 60)
    days, hours = divmod(total_hours, 24)
    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h"


def _extract_available_balance(account_summary: dict | None) -> Decimal | None:
    payload = dict(account_summary or {})
    for key in BALANCE_KEYS:
        if key in payload and payload.get(key) not in (None, ""):
            return _as_decimal(payload[key], default=Decimal("0"))
    return None


def _load_latest_snapshots(bot_ids: list[str], *, session=None) -> dict[str, BotEquitySnapshot]:
    session = session or db.session
    if not bot_ids:
        return {}

    snapshots = (
        session.query(BotEquitySnapshot)
        .filter(BotEquitySnapshot.bot_id.in_(bot_ids))
        .order_by(BotEquitySnapshot.snapshot_date.desc(), BotEquitySnapshot.updated_at.desc())
        .all()
    )

    latest_by_bot: dict[str, BotEquitySnapshot] = {}
    for snapshot in snapshots:
        latest_by_bot.setdefault(snapshot.bot_id, snapshot)
    return latest_by_bot


def _serialize_recent_bot(bot: BotInstance, *, strategy_name: str, latest_snapshot: BotEquitySnapshot | None) -> dict:
    profit = float(latest_snapshot.total_profit) if latest_snapshot is not None else float(bot.profit or 0)
    return {
        "id": bot.id,
        "name": bot.name,
        "strategy": strategy_name,
        "status": bot.status,
        "profit": profit,
        "runtime": _format_runtime(bot.created_at),
        "capital": float(bot.capital or 0),
        "tags": list(bot.tags or []),
    }


def _serialize_bot_detail(
    bot: BotInstance,
    *,
    strategy_name: str,
    integration: UserIntegration | None,
    latest_snapshot: BotEquitySnapshot | None,
) -> dict:
    capital = float(bot.capital or 0)
    profit = float(latest_snapshot.total_profit) if latest_snapshot is not None else float(bot.profit or 0)
    total_return_rate = float(latest_snapshot.total_return_rate) if latest_snapshot is not None else (profit / capital if capital else 0.0)
    return {
        "id": bot.id,
        "name": bot.name,
        "strategy": strategy_name,
        "strategy_id": bot.strategy_id,
        "strategy_name": strategy_name,
        "integration_id": bot.integration_id,
        "integration_display_name": integration.display_name if integration is not None else "",
        "status": bot.status,
        "profit": profit,
        "total_return_rate": total_return_rate,
        "runtime": _format_runtime(bot.created_at),
        "capital": capital,
        "tags": list(bot.tags or []),
        "paper": bool(bot.paper),
        "created_at": format_beijing_iso_ms(bot.created_at),
        "last_error_message": bot.last_error_message,
    }


def get_bot_for_user(bot_id: str, user_id: str, *, session=None) -> BotInstance | None:
    session = session or db.session
    return (
        session.query(BotInstance)
        .filter(
            BotInstance.id == bot_id,
            BotInstance.user_id == user_id,
            BotInstance.deleted_at.is_(None),
        )
        .first()
    )


def create_bot(*, user_id: str, payload: dict, session=None) -> dict:
    session = session or db.session
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise BotServiceError("USER_NOT_FOUND", "User not found", 404)

    strategy_id = str(payload.get("strategy_id") or "").strip()
    integration_id = str(payload.get("integration_id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not strategy_id:
        raise BotServiceError("VALIDATION_ERROR", "strategy_id is required", 422)
    if not integration_id:
        raise BotServiceError("VALIDATION_ERROR", "integration_id is required", 422)

    try:
        capital = _as_decimal(payload.get("capital"))
    except (InvalidOperation, TypeError, ValueError):
        raise BotServiceError("VALIDATION_ERROR", "capital must be numeric", 422)
    if capital < MIN_BOT_CAPITAL:
        raise BotServiceError("VALIDATION_ERROR", f"capital must be at least {MIN_BOT_CAPITAL}", 422)

    strategy = (
        session.query(Strategy)
        .filter(
            Strategy.id == strategy_id,
            Strategy.owner_id == user_id,
            Strategy.deleted_at.is_(None),
        )
        .first()
    )
    if strategy is None:
        raise BotServiceError("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    integration = integrations_service.get_user_integration(integration_id, user_id, session=session)
    if integration is None:
        raise BotServiceError("INTEGRATION_NOT_FOUND", "Integration not found", 404)

    provider = session.get(IntegrationProvider, integration.provider_key)
    if provider is None or provider.type != "broker_account":
        raise BotServiceError("INVALID_INTEGRATION", "Only broker_account integrations can host bots", 422)

    slot_limit = get_bot_slot_limit(user.plan_level)
    active_count = (
        session.query(BotInstance)
        .filter(
            BotInstance.user_id == user_id,
            BotInstance.status.in_(ACTIVE_BOT_STATUSES),
            BotInstance.deleted_at.is_(None),
        )
        .count()
    )
    if active_count >= slot_limit:
        raise BotServiceError(
            "BOT_SLOT_LIMIT_REACHED",
            f"Current plan supports at most {slot_limit} active custody bots",
            403,
        )

    integrations_service.attach_secret_payload(integration, session=session)
    adapter = integrations_service.get_broker_adapter(integration.provider_key)
    account_summary = adapter.get_account_summary(integration)
    available_balance = _extract_available_balance(account_summary)
    if available_balance is not None and capital > available_balance:
        raise BotServiceError("CAPITAL_EXCEEDS_AVAILABLE_BALANCE", "capital exceeds available account balance", 422)

    strategy_name = strategy.title or strategy.name
    bot = BotInstance(
        name=name or strategy_name,
        strategy=strategy_name,
        strategy_id=strategy.id,
        integration_id=integration.id,
        status="active",
        profit=0.0,
        runtime="0h",
        capital=float(capital),
        tags=[integration.display_name, integration.provider_key],
        paper=False,
        user_id=user_id,
    )
    session.add(bot)
    session.flush()

    snapshot = BotEquitySnapshot(
        bot_id=bot.id,
        snapshot_date=date.today(),
        equity=capital.quantize(Decimal("0.01")),
        available_cash=capital.quantize(Decimal("0.01")),
        position_value=Decimal("0.00"),
        total_profit=Decimal("0.00"),
        total_return_rate=Decimal("0.000000"),
    )
    session.add(snapshot)
    session.commit()
    return _serialize_bot_detail(bot, strategy_name=strategy_name, integration=integration, latest_snapshot=snapshot)


def list_bots(user_id: str, *, session=None) -> list[dict]:
    session = session or db.session
    bots = (
        session.query(BotInstance)
        .filter(
            BotInstance.user_id == user_id,
            BotInstance.deleted_at.is_(None),
        )
        .order_by(BotInstance.created_at.desc(), BotInstance.id.desc())
        .all()
    )
    if not bots:
        return []

    strategy_ids = [bot.strategy_id for bot in bots if bot.strategy_id]
    integration_ids = [bot.integration_id for bot in bots if bot.integration_id]
    strategies = session.query(Strategy).filter(Strategy.id.in_(strategy_ids)).all() if strategy_ids else []
    integrations = session.query(UserIntegration).filter(UserIntegration.id.in_(integration_ids)).all() if integration_ids else []
    strategy_map = {item.id: item for item in strategies}
    integration_map = {item.id: item for item in integrations}
    latest_snapshots = _load_latest_snapshots([bot.id for bot in bots], session=session)

    return [
        _serialize_bot_detail(
            bot,
            strategy_name=((strategy_map.get(bot.strategy_id).title or strategy_map.get(bot.strategy_id).name) if strategy_map.get(bot.strategy_id) else bot.strategy),
            integration=integration_map.get(bot.integration_id),
            latest_snapshot=latest_snapshots.get(bot.id),
        )
        for bot in bots
    ]


def list_recent_bots(user_id: str, *, limit: int = 10, session=None) -> list[dict]:
    session = session or db.session
    bots = (
        session.query(BotInstance)
        .filter(
            BotInstance.user_id == user_id,
            BotInstance.deleted_at.is_(None),
        )
        .order_by(BotInstance.created_at.desc(), BotInstance.id.desc())
        .limit(limit)
        .all()
    )
    if not bots:
        return []

    strategy_ids = [bot.strategy_id for bot in bots if bot.strategy_id]
    strategies = session.query(Strategy).filter(Strategy.id.in_(strategy_ids)).all() if strategy_ids else []
    strategy_map = {item.id: item for item in strategies}
    latest_snapshots = _load_latest_snapshots([bot.id for bot in bots], session=session)

    return [
        _serialize_recent_bot(
            bot,
            strategy_name=((strategy_map.get(bot.strategy_id).title or strategy_map.get(bot.strategy_id).name) if strategy_map.get(bot.strategy_id) else bot.strategy),
            latest_snapshot=latest_snapshots.get(bot.id),
        )
        for bot in bots
    ]


def update_bot_status(*, bot: BotInstance, status: str, session=None) -> dict:
    session = session or db.session
    if status not in ALLOWED_STATUSES:
        raise BotServiceError("VALIDATION_ERROR", f"status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}", 422)

    if status == "active" and bot.status != "active":
        user = session.get(User, bot.user_id)
        slot_limit = get_bot_slot_limit(user.plan_level if user is not None else "free")
        active_count = (
            session.query(BotInstance)
            .filter(
                BotInstance.user_id == bot.user_id,
                BotInstance.status.in_(ACTIVE_BOT_STATUSES),
                BotInstance.deleted_at.is_(None),
                BotInstance.id != bot.id,
            )
            .count()
        )
        if active_count >= slot_limit:
            raise BotServiceError(
                "BOT_SLOT_LIMIT_REACHED",
                f"Current plan supports at most {slot_limit} active custody bots",
                403,
            )

    bot.status = status
    bot.updated_at = now_ms()
    session.commit()
    return {"id": bot.id, "status": bot.status}


def get_bot_positions(*, bot: BotInstance, session=None) -> list[dict]:
    session = session or db.session
    orders = (
        session.query(Order)
        .filter(Order.bot_id == bot.id, Order.status == "filled")
        .order_by(Order.timestamp.asc(), Order.created_at.asc())
        .all()
    )

    aggregate: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "quantity": Decimal("0"),
            "avg_cost": Decimal("0"),
            "last_price": Decimal("0"),
            "realized_pnl": Decimal("0"),
        }
    )

    for order in orders:
        item = aggregate[order.symbol]
        quantity = _as_decimal(order.quantity, default=Decimal("0"))
        price = _as_decimal(order.price, default=Decimal("0"))
        if order.side == "buy":
            current_qty = item["quantity"]
            next_qty = current_qty + quantity
            if next_qty > 0:
                item["avg_cost"] = ((current_qty * item["avg_cost"]) + (quantity * price)) / next_qty if current_qty > 0 else price
            item["quantity"] = next_qty
        elif order.side == "sell":
            item["quantity"] = max(Decimal("0"), item["quantity"] - quantity)
            item["realized_pnl"] += _as_decimal(order.pnl, default=Decimal("0"))
        item["last_price"] = price

    payload = []
    for symbol in sorted(aggregate):
        item = aggregate[symbol]
        if item["quantity"] <= 0:
            continue
        market_value = item["quantity"] * item["last_price"]
        payload.append(
            {
                "symbol": symbol,
                "quantity": f"{item['quantity']:.4f}",
                "avg_cost": f"{item['avg_cost']:.4f}",
                "market_value": f"{market_value:.4f}",
                "realized_pnl": f"{item['realized_pnl']:.4f}",
            }
        )
    return payload


def get_bot_performance(*, bot: BotInstance, session=None) -> dict:
    session = session or db.session
    snapshots = (
        session.query(BotEquitySnapshot)
        .filter(BotEquitySnapshot.bot_id == bot.id)
        .order_by(BotEquitySnapshot.snapshot_date.asc(), BotEquitySnapshot.updated_at.asc())
        .all()
    )
    latest_snapshot = snapshots[-1] if snapshots else None
    orders = (
        session.query(Order)
        .filter(Order.bot_id == bot.id)
        .order_by(Order.timestamp.desc(), Order.created_at.desc())
        .all()
    )

    latest_equity = float(latest_snapshot.equity) if latest_snapshot is not None else float(bot.capital or 0)
    total_profit = float(latest_snapshot.total_profit) if latest_snapshot is not None else float(bot.profit or 0)
    total_return_rate = float(latest_snapshot.total_return_rate) if latest_snapshot is not None else (total_profit / float(bot.capital or 1) if bot.capital else 0.0)

    return {
        "summary": {
            "latest_equity": latest_equity,
            "total_profit": total_profit,
            "total_return_rate": total_return_rate,
        },
        "equity_curve": [
            {
                "snapshot_date": snapshot.snapshot_date.isoformat(),
                "equity": float(snapshot.equity),
                "available_cash": float(snapshot.available_cash),
                "position_value": float(snapshot.position_value),
                "total_profit": float(snapshot.total_profit),
                "total_return_rate": float(snapshot.total_return_rate),
            }
            for snapshot in snapshots
        ],
        "orders": [
            {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "price": order.price,
                "quantity": order.quantity,
                "status": order.status,
                "pnl": order.pnl,
                "timestamp": order.timestamp,
                "client_order_id": order.client_order_id,
            }
            for order in orders
        ],
    }
