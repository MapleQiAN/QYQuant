# Flask Backend MVP Design (QYQuant)

Date: 2026-01-30
Owner: Backend Lead

## Goals
- Provide a Flask MVP backend that matches frontend types and endpoints exactly.
- Use a consistent response envelope and error format.
- Support backtest and bot task loops with Celery + Redis.
- Provide a usable local dev stack with Postgres + Redis.

## Key Decisions
- Database: Postgres only (docker-compose).
- Timestamps: Unix milliseconds across all APIs and stored as bigint.
- Response envelope: { code, message, data, request_id? } for success.
- Error format: HTTP status + business code + message + optional details.
- Frontend: request layer will unwrap envelope data.
- Storage: local disk for files under backend/storage.

## Architecture
- App factory pattern with module blueprints:
  auth, users, strategies, backtests, bots, forum, files.
- Common extensions: SQLAlchemy, Alembic, Marshmallow, JWT, CORS.
- Central error handler for normalization and request_id logging.
- OpenAPI via Flask-Smorest and a static docs/api-contract.md.

## Data Model (Tables)
- users
- strategies
- strategy_versions
- backtests
- backtest_trades
- bot_instances
- orders
- posts
- comments
- likes
- favorites
- tips
- files
- follows

Fields align to frontend types:
- Strategy: id, name, symbol, status, returns, winRate, maxDrawdown, tags, lastUpdate, trades
- Bot: id, name, strategy, status, profit, runtime, capital, tags
- Post: id, title, author, avatar, likes, comments, timestamp, tags
- Backtest: id, name, symbol, status, startedAt, finishedAt, summary
- BacktestLatestResponse: summary, kline, trades

## Backtest Loop (MVP)
- POST /api/backtests/run -> create backtest + celery job, return job_id.
- GET /api/backtests/job/<job_id> -> status (PENDING/RUNNING/SUCCESS/FAILED) + result on success.
- GET /api/backtests/latest -> latest overview (KPI + KlineBars + TradeMarkers).
- Built-in strategies: SMA crossover, RSI.
- DataProvider abstraction: MockProvider, CSVProvider.

## Bot Hosting (Paper Trading MVP)
- POST /api/bots -> create bot instance (paper=true).
- GET /api/bots/recent
- PATCH /api/bots/<id>/status -> running/paused
- GET /api/bots/<id>/performance -> equity curve + orders (mock ok)
- Orders table records each simulated order with idempotency key.

## Forum MVP
- GET /api/forum/hot
- CRUD: posts/comments/likes/favorites/tips
- tips only records amounts; no payment integration.

## Files
- POST /api/files -> upload (type/size constraints, auth required)
- GET /api/files/<id> -> download (auth + owner check)
- Store local under backend/storage with metadata in files table.

## Auth and Security
- JWT login: POST /api/auth/login (seed user admin/admin123).
- GET /api/users/me returns current user.
- Encrypted storage placeholder for API keys (Fernet).
- Strategy upload execution not implemented; TODO for sandboxing.

## Testing
- Pytest covers error normalization, backtest job lifecycle, and 8+ key endpoints.
- Provide seed data script for local demo.

## Dev UX
- docker-compose: postgres + redis
- Commands: make dev, flask run, celery worker

## Frontend Integration
- Set VITE_API_BASE to http://localhost:5000/api
- Disable MSW; request layer unwraps envelope data
