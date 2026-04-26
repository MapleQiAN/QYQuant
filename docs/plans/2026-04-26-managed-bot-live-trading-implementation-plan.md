# Managed Bot Live Trading Implementation Plan

Date: 2026-04-26

## Current State

The managed bot feature is not ready for real live trading yet.

Completed:

- Users can create broker integrations and store secret payloads encrypted.
- Broker integrations expose validation, account summary, and position reads.
- Users can create managed bot records tied to a strategy and broker integration.
- Managed bots can be listed, paused, resumed, and inspected.
- Initial equity snapshots and dashboard fields exist.
- Simulation bots have a separate scheduled execution loop with persisted records, trades, and positions.

Missing:

- No broker order contract exists.
- No adapter exposes place order, cancel order, query order, or fills.
- No scheduled execution task runs managed bots.
- No service turns strategy output into live orders.
- No risk gate protects real orders before submission.
- No reconciliation loop syncs broker state back into local orders, positions, and equity snapshots.
- No live-trading tests cover order execution, idempotency, retries, or broker failures.

## Goal

Make managed bots usable as controlled live-trading bots after a user connects a supported broker API.

The first production-ready version should support:

- Broker account read.
- Strategy signal execution on a schedule.
- Pre-trade risk checks.
- Idempotent order submission.
- Order status and fill synchronization.
- Equity snapshot refresh.
- Pause/resume behavior that prevents new orders when paused.
- Clear failure states and audit trail.

## Non-Goals For First Version

- Multi-broker smart order routing.
- Intraday high-frequency execution.
- Options, futures, margin, short selling, or derivatives.
- Fully automated recovery from every broker outage.
- Portfolio optimizer across multiple bots.
- Frontend-heavy trade blotter redesign.

## Proposed Architecture

### Broker Execution Contract

Extend `BrokerAccountAdapter` with live order methods:

- `place_order(integration, order_request) -> order_response`
- `cancel_order(integration, broker_order_id) -> cancel_response`
- `get_order(integration, broker_order_id) -> order_status`
- `list_orders(integration, since=None) -> list[order_status]`
- `get_fills(integration, since=None) -> list[fill]`

Keep read methods:

- `validate_credentials(config)`
- `get_account_summary(integration)`
- `get_positions(integration)`

Use a normalized internal request shape:

```json
{
  "client_order_id": "string",
  "symbol": "string",
  "side": "buy|sell",
  "quantity": "decimal-string",
  "order_type": "market|limit",
  "limit_price": "decimal-string|null",
  "time_in_force": "day|gtc",
  "metadata": {
    "bot_id": "string",
    "strategy_id": "string",
    "signal_id": "string"
  }
}
```

### Execution Service

Add a managed bot execution service that:

1. Loads active `BotInstance` rows where `paper = false`.
2. Skips paused, deleted, or invalid bots.
3. Loads the strategy package for the bot owner.
4. Builds live execution context from broker account, broker positions, and market data.
5. Executes strategy in a sandbox or controlled runtime.
6. Normalizes strategy output into order intents.
7. Runs pre-trade risk checks.
8. Persists local pending `Order` rows with unique `client_order_id`.
9. Calls broker adapter `place_order`.
10. Updates local order status with broker response.
11. Writes `BotEquitySnapshot`.

### Reconciliation Service

Add a reconciliation service that:

- Pulls broker order status and fills.
- Updates local `Order.status`, fill price, fill quantity, and PnL fields.
- Detects drift between broker positions and locally aggregated positions.
- Writes the latest equity snapshot.
- Marks bot `last_error_message` when broker state cannot be reconciled.

### Celery Tasks

Add two scheduled tasks:

- `run_managed_bots`: frequent live execution task.
- `reconcile_managed_bots`: broker state sync task.

Initial schedules:

- `run_managed_bots`: every 5 minutes during the first implementation, configurable by env.
- `reconcile_managed_bots`: every 5 minutes.

Both tasks must use the `simulation` queue or a new `trading` queue. Prefer a new `trading` queue for production isolation.

## Data Model Changes

Extend `orders` or add a dedicated live order table. Prefer extending `orders` only if backward compatibility is clean.

Needed fields:

- `integration_id`
- `strategy_id`
- `broker_order_id`
- `order_type`
- `limit_price`
- `filled_quantity`
- `filled_avg_price`
- `submitted_at`
- `filled_at`
- `rejected_reason`
- `raw_broker_payload`

Add optional bot runtime fields:

- `last_run_at`
- `last_reconciled_at`
- `last_signal_at`
- `failure_count`

## Risk Controls

First version must block order submission when any check fails:

- Bot status is not `active`.
- Integration is missing or deleted.
- Broker adapter does not support live orders.
- Account summary cannot be loaded.
- Available cash is below required capital.
- Order symbol is not in the strategy manifest allowlist.
- Order value exceeds per-order cap.
- Daily bot order count exceeds configured limit.
- Total open exposure exceeds bot capital.
- Market is outside allowed trading window.
- Strategy output contains invalid side, quantity, price, or unsupported order type.

Recommended defaults:

- Default to disabled live trading unless `LIVE_TRADING_ENABLED=true`.
- Require provider capability `orders: true`.
- Require a bot-level `live_confirmed_at` or equivalent explicit confirmation before first real order.

## Implementation Phases

### Phase 1: Contracts And Storage

- Extend broker adapter base contract.
- Add normalized order request/response helpers.
- Add broker capability metadata for order support.
- Add migration for live order fields.
- Add unit tests for contract normalization and unsupported adapters.

Exit criteria:

- Unsupported adapters fail safely before order submission.
- Existing account and position reads remain compatible.

### Phase 2: Managed Bot Execution Skeleton

- Add `managed_bot_tasks.py`.
- Add execution service that loads active managed bots.
- Add dry-run mode that generates order intents without calling broker.
- Add risk gate service.
- Persist skipped, rejected, and pending order outcomes.

Exit criteria:

- A managed bot can run in dry-run mode and produce auditable decisions.
- Paused bots never generate new orders.

### Phase 3: Broker Order Adapter Implementation

- Implement real order methods for the first chosen broker.
- Add fake broker adapter for tests.
- Keep other brokers read-only until their SDK contract is confirmed.
- Add integration tests for place order, cancel order, order status, and fills through the normalized contract.

Exit criteria:

- One broker path can submit, cancel, and query normalized orders using a fake client in tests.
- Production client factory is explicitly configured, not silently mocked.

### Phase 4: Reconciliation And Snapshots

- Add reconciliation service.
- Sync local orders from broker status.
- Refresh equity snapshots from account summary.
- Compare broker positions with local aggregate and surface drift.

Exit criteria:

- Filled broker orders appear in bot performance.
- Equity curve updates from broker state.
- Drift is visible and does not silently overwrite data.

### Phase 5: Frontend Readiness

- Add explicit live-trading warning and confirmation before enabling a bot.
- Show last run time, last reconciliation time, and last error.
- Show order status details and broker order id.
- Disable "active" transition if provider does not support orders.

Exit criteria:

- User cannot accidentally enable live trading from the current create bot flow.
- Operational status is visible without reading logs.

### Phase 6: Verification And Rollout

- Add focused tests for services, tasks, adapters, and API behavior.
- Add a dry-run staging checklist.
- Add provider-specific environment setup docs.
- Keep live trading disabled by default.

Exit criteria:

- Tests pass locally.
- Dry-run produces expected audit trail.
- Live mode requires explicit env flag and explicit user confirmation.

## Test Plan

Backend:

- Adapter contract tests.
- Risk gate unit tests.
- Managed bot execution task tests.
- Reconciliation task tests.
- API status and safety tests.
- Regression tests for existing simulation bots.

Frontend:

- Create managed bot modal guards.
- Active/paused status controls.
- Live warning confirmation.
- Error and last-run display.

Manual:

- Create broker integration.
- Validate account read.
- Create managed bot in dry-run.
- Run execution task manually.
- Confirm order intents are stored but not submitted.
- Enable fake broker live mode.
- Confirm order submission and reconciliation.

## Open Decisions

- Which broker should be implemented first for real orders: XtQuant, GMTrade, or LongPort?
- Should live orders reuse `orders` or use a new `live_orders` table?
- Should strategy output use the current backtest result schema or a new live signal schema?
- Should execution cadence be fixed, strategy-defined, or market-calendar aware?
- Should first release require human approval for every generated order?

## Recommended First Implementation Slice

Start with the smallest safe slice:

1. Add broker order capability and normalized order dataclasses.
2. Add unsupported live-order behavior to all existing adapters.
3. Add a fake live-order adapter for tests.
4. Add managed bot dry-run execution service.
5. Add Celery task registration without enabling real live orders.

This produces an auditable live-trading pipeline without risking real broker orders.

