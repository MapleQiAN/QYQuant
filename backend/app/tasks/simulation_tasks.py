import logging
from datetime import date
from decimal import Decimal

from celery.exceptions import SoftTimeLimitExceeded
from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import SimulationBot, SimulationPosition, SimulationRecord, SimulationTrade
from ..strategy_runtime import StrategyRuntimeError, execute_backtest_strategy
from ..strategy_runtime.loader import load_strategy_package
from ..utils.time import now_utc

logger = logging.getLogger(__name__)


def _execute_single_bot(bot):
    loaded = load_strategy_package(bot.strategy_id, version=None)
    latest_record = (
        SimulationRecord.query
        .filter_by(bot_id=bot.id)
        .order_by(SimulationRecord.trade_date.desc())
        .first()
    )
    current_equity = Decimal(str(latest_record.equity if latest_record else bot.initial_capital))
    current_cash = Decimal(str(latest_record.cash if latest_record else bot.initial_capital))

    existing_positions = SimulationPosition.query.filter_by(bot_id=bot.id).all()
    positions_payload = {
        position.symbol: {
            'quantity': float(position.quantity),
            'avg_cost': float(position.avg_cost),
        }
        for position in existing_positions
    }

    trade_date = date.today()

    outcome = execute_backtest_strategy(
        symbol=(loaded.get('manifest') or {}).get('symbol', '000001.XSHG'),
        bars=[],
        loaded_strategy=loaded,
        params={
            'mode': 'simulation',
            'current_equity': float(current_equity),
            'current_cash': float(current_cash),
            'positions': positions_payload,
            'trade_date': str(trade_date),
        },
        timeout_seconds=120,
    )
    new_equity = Decimal(str(outcome.get('equity', current_equity)))
    new_cash = Decimal(str(outcome.get('cash', current_cash)))
    previous_equity = current_equity
    daily_return = Decimal('0') if previous_equity == 0 else (new_equity - previous_equity) / previous_equity

    record = SimulationRecord.query.filter_by(bot_id=bot.id, trade_date=trade_date).first()
    if record is None:
        record = SimulationRecord(
            bot_id=bot.id,
            trade_date=trade_date,
        )
        db.session.add(record)
    record.equity = new_equity
    record.cash = new_cash
    record.daily_return = daily_return

    new_positions = outcome.get('positions')
    if isinstance(new_positions, dict):
        existing_by_symbol = {position.symbol: position for position in existing_positions}
        incoming_symbols = set(new_positions.keys())

        for symbol, payload in new_positions.items():
            quantity = Decimal(str(payload.get('quantity', 0)))
            avg_cost = Decimal(str(payload.get('avg_cost', 0)))
            position = existing_by_symbol.get(symbol)
            if position is None:
                position = SimulationPosition(bot_id=bot.id, symbol=symbol)
                db.session.add(position)
            position.quantity = quantity
            position.avg_cost = avg_cost
            position.updated_at = now_utc()

        for symbol, position in existing_by_symbol.items():
            if symbol not in incoming_symbols:
                db.session.delete(position)

    raw_trades = outcome.get('trades') or []
    for payload in raw_trades:
        db.session.add(
            SimulationTrade(
                bot_id=bot.id,
                trade_date=trade_date,
                symbol=str(payload.get('symbol', '')),
                side=str(payload.get('side', 'buy')),
                price=Decimal(str(payload.get('price', 0))),
                quantity=Decimal(str(payload.get('quantity', 0))),
            )
        )

    db.session.commit()
    logger.info(
        "[simulation] bot=%s trade_date=%s equity=%s daily_return=%s",
        bot.id,
        trade_date,
        new_equity,
        daily_return,
    )


def _run_daily_simulation():
    active_bots = SimulationBot.query.filter(
        SimulationBot.status == 'active',
        SimulationBot.deleted_at.is_(None),
    ).all()
    logger.info("[simulation] starting daily run for %s active bots", len(active_bots))

    processed = 0
    for bot in active_bots:
        try:
            _execute_single_bot(bot)
            processed += 1
        except SoftTimeLimitExceeded:
            db.session.rollback()
            logger.error("[simulation] bot=%s timed out", bot.id)
        except StrategyRuntimeError as exc:
            db.session.rollback()
            logger.error("[simulation] bot=%s strategy error: %s %s", bot.id, exc.message, exc.details)
        except Exception:
            db.session.rollback()
            logger.exception("[simulation] bot=%s unexpected error", bot.id)

    return {'processed': processed}


@celery_app.task(bind=True, name='app.tasks.simulation_tasks.run_daily_simulation')
def run_daily_simulation(self):
    if has_app_context():
        return _run_daily_simulation()

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _run_daily_simulation()
