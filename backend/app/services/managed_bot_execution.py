from decimal import Decimal, InvalidOperation

from ..extensions import db
from ..models import BotInstance, IntegrationProvider, Order
from ..strategy_runtime import StrategyRuntimeError, execute_backtest_strategy
from ..strategy_runtime.loader import load_strategy_package
from ..utils.time import now_ms
from . import integrations as integrations_service


ACTIVE_MANAGED_BOT_STATUSES = ("active", "running")
DRY_RUN_ORDER_STATUS = "dry_run"
REJECTED_ORDER_STATUS = "rejected"


class ManagedBotExecutionError(Exception):
    pass


def _as_decimal(value, *, default: Decimal | None = None) -> Decimal:
    if value is None:
        if default is not None:
            return default
        raise InvalidOperation("missing decimal value")
    return Decimal(str(value))


def _normalize_order_intent(payload: dict, *, default_symbol: str) -> dict:
    symbol = str(payload.get("symbol") or default_symbol or "").strip()
    side = str(payload.get("side") or "").strip().lower()
    if side not in {"buy", "sell"}:
        raise ManagedBotExecutionError(f"unsupported order side: {side}")

    quantity = _as_decimal(payload.get("quantity"))
    if quantity <= 0:
        raise ManagedBotExecutionError("order quantity must be positive")

    price = _as_decimal(payload.get("price"), default=Decimal("0"))
    if price < 0:
        raise ManagedBotExecutionError("order price cannot be negative")

    order_type = str(payload.get("order_type") or payload.get("type") or "market").strip().lower()
    if order_type not in {"market", "limit"}:
        raise ManagedBotExecutionError(f"unsupported order type: {order_type}")

    limit_price = payload.get("limit_price")
    normalized_limit_price = None if limit_price is None else float(_as_decimal(limit_price))
    if order_type == "limit" and normalized_limit_price is None:
        raise ManagedBotExecutionError("limit order requires limit_price")

    return {
        "symbol": symbol,
        "side": side,
        "quantity": float(quantity),
        "price": float(price),
        "order_type": order_type,
        "limit_price": normalized_limit_price,
    }


def _reject_reason_for_intent(intent: dict, *, allowed_symbols: set[str]) -> str | None:
    if intent["symbol"] not in allowed_symbols:
        return "symbol_not_allowed"
    if intent["quantity"] <= 0:
        return "quantity_not_positive"
    if intent["price"] < 0:
        return "price_negative"
    return None


def _fallback_rejected_intent(payload: dict, *, default_symbol: str) -> dict:
    return {
        "symbol": str(payload.get("symbol") or default_symbol or "UNKNOWN"),
        "side": str(payload.get("side") or "unknown"),
        "quantity": 0.0,
        "price": 0.0,
        "order_type": str(payload.get("order_type") or payload.get("type") or "market"),
        "limit_price": None,
    }


def _extract_order_intents(outcome: dict) -> list[dict]:
    if isinstance(outcome.get("orders"), list):
        return outcome["orders"]
    if isinstance(outcome.get("trades"), list):
        return outcome["trades"]
    return []


def _load_active_managed_bots(session) -> list[BotInstance]:
    return (
        session.query(BotInstance)
        .filter(
            BotInstance.paper.is_(False),
            BotInstance.status.in_(ACTIVE_MANAGED_BOT_STATUSES),
            BotInstance.deleted_at.is_(None),
        )
        .order_by(BotInstance.created_at.asc(), BotInstance.id.asc())
        .all()
    )


def execute_managed_bot_dry_run(*, bot: BotInstance, run_started_at: int | None = None, session=None) -> dict:
    session = session or db.session
    run_started_at = run_started_at or now_ms()
    if bot.status not in ACTIVE_MANAGED_BOT_STATUSES or bot.deleted_at is not None:
        return {"bot_id": bot.id, "status": "skipped", "reason": "bot_not_active", "orders": 0}

    integration = integrations_service.get_user_integration(bot.integration_id, bot.user_id, session=session)
    if integration is None:
        raise ManagedBotExecutionError("integration_not_found")

    provider = session.get(IntegrationProvider, integration.provider_key)
    if provider is None or provider.type != "broker_account":
        raise ManagedBotExecutionError("invalid_broker_integration")

    integrations_service.attach_secret_payload(integration, session=session)
    adapter = integrations_service.get_broker_adapter(integration.provider_key)
    account_summary = adapter.get_account_summary(integration)
    broker_positions = adapter.get_positions(integration)

    loaded = load_strategy_package(bot.strategy_id, version=None, user_id=bot.user_id)
    manifest = loaded.get("manifest") or {}
    default_symbol = manifest.get("symbol") or "000001.XSHG"
    outcome = execute_backtest_strategy(
        default_symbol,
        [],
        loaded,
        {
            "mode": "managed_dry_run",
            "bot_id": bot.id,
            "capital": bot.capital,
            "account_summary": account_summary,
            "broker_positions": broker_positions,
        },
        timeout_seconds=120,
    )
    if outcome.get("ok") is False:
        raise ManagedBotExecutionError(outcome.get("error") or outcome.get("error_code") or "strategy_failed")

    raw_intents = _extract_order_intents(outcome)
    persisted = 0
    rejected = 0
    allowed_symbols = {default_symbol}
    for index, raw_intent in enumerate(raw_intents):
        client_order_id = f"{bot.id}:dry-run:{run_started_at}:{index}"
        existing = session.query(Order).filter_by(client_order_id=client_order_id).first()
        if existing is not None:
            continue
        rejected_reason = None
        try:
            intent = _normalize_order_intent(raw_intent, default_symbol=default_symbol)
            rejected_reason = _reject_reason_for_intent(intent, allowed_symbols=allowed_symbols)
        except ManagedBotExecutionError as exc:
            intent = _fallback_rejected_intent(raw_intent, default_symbol=default_symbol)
            rejected_reason = str(exc)
        status = REJECTED_ORDER_STATUS if rejected_reason else DRY_RUN_ORDER_STATUS
        session.add(
            Order(
                bot_id=bot.id,
                integration_id=integration.id,
                strategy_id=bot.strategy_id,
                symbol=intent["symbol"],
                side=intent["side"],
                price=intent["price"],
                quantity=intent["quantity"],
                status=status,
                timestamp=run_started_at,
                client_order_id=client_order_id,
                order_type=intent["order_type"],
                limit_price=intent["limit_price"],
                rejected_reason=rejected_reason,
                raw_broker_payload={
                    "mode": "managed_dry_run",
                    "source": "strategy_runtime",
                    "raw_intent": dict(raw_intent),
                },
            )
        )
        if rejected_reason:
            rejected += 1
        else:
            persisted += 1

    bot.last_run_at = run_started_at
    bot.last_signal_at = run_started_at if persisted else bot.last_signal_at
    bot.last_error_message = None
    bot.failure_count = 0
    bot.updated_at = run_started_at
    session.commit()
    return {"bot_id": bot.id, "status": "dry_run_completed", "orders": persisted, "rejected": rejected}


def run_managed_bots_dry_run(*, session=None) -> dict:
    session = session or db.session
    bots = _load_active_managed_bots(session)
    processed = 0
    failed = 0
    skipped = 0
    for bot in bots:
        try:
            result = execute_managed_bot_dry_run(bot=bot, session=session)
            if result["status"] == "skipped":
                skipped += 1
            else:
                processed += 1
        except (ManagedBotExecutionError, StrategyRuntimeError) as exc:
            session.rollback()
            bot = session.get(BotInstance, bot.id)
            if bot is not None:
                bot.failure_count = int(bot.failure_count or 0) + 1
                bot.last_error_message = str(exc)
                bot.last_run_at = now_ms()
                bot.updated_at = bot.last_run_at
                session.commit()
            failed += 1
        except Exception as exc:
            session.rollback()
            bot = session.get(BotInstance, bot.id)
            if bot is not None:
                bot.failure_count = int(bot.failure_count or 0) + 1
                bot.last_error_message = str(exc)
                bot.last_run_at = now_ms()
                bot.updated_at = bot.last_run_at
                session.commit()
            failed += 1
    return {"processed": processed, "failed": failed, "skipped": skipped}
