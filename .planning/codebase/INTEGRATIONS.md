# External Integrations

**Analysis Date:** 2026-04-27

## APIs & External Services

### Market Data Providers

**Binance API:**
- Purpose: Real-time cryptocurrency kline (OHLCV) data and latest prices
- SDK/Client: Custom `BinanceClient` at `backend/app/marketdata/binance.py`
- Config: `BINANCE_BASE_URL` (default `https://api.binance.com`), `BINANCE_API_TIMEOUT`, `BINANCE_KLINE_CACHE_TTL`, `BINANCE_PRICE_CACHE_TTL`
- Used by: Backtest engine for crypto symbols (via `BinanceProvider` at `backend/app/backtest/providers.py`)
- Cache: Redis-backed caching for kline and price data

**FreeGold API:**
- Purpose: XAUUSD (gold) price data
- SDK/Client: Custom `FreeGoldClient` at `backend/app/marketdata/freegold.py`
- Config: `FREEGOLD_BASE_URL` (default `https://freegoldapi.com`), `FREEGOLD_API_TIMEOUT`, `FREEGOLD_DATA_CACHE_TTL`, `FREEGOLD_INTERVAL`
- Cache: Redis-backed with 6-hour default TTL

**Sina Gold (Sina Finance):**
- Purpose: Alternative gold price data source (preferred over FreeGold for auto mode)
- SDK/Client: Custom `SinaGoldClient` at `backend/app/marketdata/sina_gold.py`
- Config: `SINA_GOLD_INTERVAL` (default `1d`)
- Cache: Redis-backed

**JoinQuant (JQData):**
- Purpose: Chinese A-share daily OHLCV historical data
- SDK/Client: `jqdatasdk` package, wrapped in `JoinQuantClient` at `backend/app/providers/joinquant.py`
- Auth: `JQDATA_USERNAME`, `JQDATA_PASSWORD`
- Config: `JQDATA_REQUEST_TIMEOUT_SECONDS` (default 3), `JQDATA_MAX_RETRIES` (default 2)
- Integration adapter: `backend/app/integrations/market_data/joinquant.py`
- Health monitoring: Celery beat task `check_jqdata_health` runs every 5 minutes

**AkShare:**
- Purpose: Chinese A-share stocks, futures, and fund data (history + real-time quotes)
- SDK/Client: `akshare` package, wrapped in `AkShareClient` at `backend/app/providers/akshare.py`
- Auth: None required (public data API)
- Integration adapter: `backend/app/integrations/market_data/akshare_like.py`
- Capabilities: `daily_bars`, `latest_quote`, `futures_quote`, `fund_nav`

**Market Data Auto-Selection:**
- `AutoProvider` at `backend/app/backtest/providers.py` routes gold symbols (XAUUSD, XAU, GOLD, GCF) to `SinaGoldProvider`, all others to `BinanceProvider`
- Config: `BACKTEST_DATA_PROVIDER` env var (values: `mock`, `auto`, `freegold`, `sinagold`, `binance`, `joinquant`, `akshare`)

### AI / LLM Services

**OpenAI-Compatible LLM:**
- Purpose: Strategy review, AI strategy generation, report narrative, intent classification
- SDK/Client: Direct HTTP via `urllib.request` at `backend/app/report_agent/llm_client.py`; credential validation via `OpenAICompatibleLLMAdapter` at `backend/app/integrations/llm/openai_compatible.py`
- Auth: User-provided API key (stored encrypted in database, decrypted per-request)
- Config per user: `base_url`, `model`, `api_key` (secret)
- Used by: `backend/app/report_agent/` (advisor, diagnostician, narrator, orchestrator), `backend/app/services/ai_strategy_generation.py`, `backend/app/services/strategy_review.py`, `backend/app/services/intent_classifier.py`

**OpenAI Agents SDK:**
- Purpose: AI agent orchestration for report generation
- Package: `openai-agents>=0.14.6`
- Entry: `backend/app/report_agent/agents_sdk.py`

**System-Level AI Config (for automated review):**
- Config: `REVIEW_AI_PROVIDER`, `REVIEW_AI_MODEL` (default `gpt-4o-mini`), `REVIEW_AI_API_KEY`, `REVIEW_AI_BASE_URL`
- Defined in: `backend/app/config.py`

### Code Execution Sandboxes

**E2B Code Interpreter:**
- Purpose: Remote sandbox execution of user strategy code
- Package: `e2b-code-interpreter>=1.5.1`
- Auth: `E2B_API_KEY`
- Config: `BACKTEST_SANDBOX_MODE` (set to enable/disable), `E2B_WARM_POOL_SIZE`
- Implementation: `backend/app/services/sandbox.py`
- Fallback: Local subprocess/inline execution when E2B is unavailable

## Data Storage

**Databases:**
- PostgreSQL 15 (Alpine Docker image)
  - Connection: `DATABASE_URL` (format: `postgresql+psycopg://user:pass@host:5432/dbname`)
  - ORM: SQLAlchemy via flask-sqlalchemy
  - Migrations: Flask-Migrate (Alembic) in `backend/migrations/`
  - Features used: JSONB, TSVECTOR (full-text search)

**Caching:**
- Redis 7 (Alpine Docker image)
  - Connection: `REDIS_URL` (default Redis DB 0 for cache)
  - Client: `redis` Python package
  - Auth store: Redis DB 0 for SMS verification codes
  - Celery broker: Redis DB 1

**File Storage:**
- Local filesystem with Docker volume `backend_storage`
  - Config: `FILE_STORAGE_DIR`
  - Mount: `/app/backend/storage` in containers

## Authentication & Identity

**Custom JWT Authentication:**
- Implementation: `flask-jwt-extended` with access tokens + refresh tokens
- Access token TTL: Configurable via `JWT_ACCESS_TOKEN_MINUTES` (default 60 min)
- Refresh token TTL: Configurable via `JWT_REFRESH_TOKEN_DAYS` (default 30 days)
- Token storage: Access tokens in frontend `localStorage` (key: `qyquant-token`); refresh tokens as HTTP cookies
- Auth flow: Login via phone+SMS code, email+password, or OAuth
- SMS verification: Configurable fixed code for dev (`AUTH_FIXED_SMS_CODE`)

**OAuth Providers:**
- WeChat - QR connect login
  - Config: `OAUTH_WECHAT_CLIENT_ID`, `OAUTH_WECHAT_CLIENT_SECRET`
- GitHub - OAuth app login
  - Config: `OAUTH_GITHUB_CLIENT_ID`, `OAUTH_GITHUB_CLIENT_SECRET`
- Google - OAuth2 login
  - Config: `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`
- Implementation: `backend/app/utils/oauth.py` using `authlib`
- Blueprint: `backend/app/blueprints/auth.py`

**Encryption:**
- Fernet symmetric encryption for user integration secrets
  - Config: `FERNET_KEY`
  - Implementation: `backend/app/utils/crypto.py` (`encrypt_text`, `decrypt_text`)
- Strategy encryption key: `STRATEGY_ENCRYPT_KEY` (base64 encoded)

## Broker Integrations

**LongPort:**
- Purpose: Hong Kong / US stock broker account connection
- Type: Hosted service
- Adapter: `backend/app/integrations/brokers/longport.py`
- Auth: `app_key`, `app_secret`, `access_token` (all secret)
- Capabilities: Account summary, positions (orders not supported)

**GMTrade (GM Quant):**
- Purpose: Chinese mainland broker account connection
- Type: Hosted service
- Adapter: `backend/app/integrations/brokers/gmtrade.py`
- Auth: `token` (secret), `account_id` + `endpoint` (public)
- Capabilities: Account summary, positions (orders not supported)

**XtQuant:**
- Purpose: Chinese mainland broker account via local connector
- Type: Local connector (requires local XtQuant client running)
- Adapter: `backend/app/integrations/brokers/xtquant.py`
- Auth: `endpoint` + `account_id` + `client_path` (all public config)
- Capabilities: Account summary, positions (orders not supported)

**Broker Registry:**
- All brokers registered in `backend/app/integrations/registry.py`
- Service layer: `backend/app/services/integrations.py`
- Integration provider catalog synced to database via `sync_provider_catalog()`

## Task Queue & Scheduling

**Celery:**
- Broker: Redis DB 1 (`CELERY_BROKER_URL`)
- Result backend: Redis DB 1 (`CELERY_RESULT_BACKEND`)
- Worker concurrency: Configurable via `CELERYD_CONCURRENCY` (default 10)
- Time limits: Soft 300s, hard 330s
- Queue routing:
  - `backtest` queue: Backtest tasks, report generation
  - `notification` queue: Notification tasks
  - `review` queue: Strategy review tasks
  - `trading` queue: Managed bot tasks
  - `simulation` queue: Simulation tasks
  - `default` queue: Everything else
- Beat schedule:
  - Daily simulation: 08:00 UTC
  - Managed bot dry run: Every 5 minutes
  - Monthly quota reset: 1st of month at 00:00 UTC
  - JQData health check: Every 5 minutes
- Task modules: `backend/app/tasks/` (backtests, data_source_tasks, managed_bot_tasks, moderation_tasks, notification_tasks, quota_tasks, report_generation, review_tasks, simulation_tasks)

## Payment System

**Payment Providers:**
- WeChat Pay - In-progress (provider key: `wechat`)
- Alipay - In-progress (provider key: `alipay`)
- Sandbox mode: Configurable via `PAYMENT_SANDBOX` (default `true`)
- Blueprint: `backend/app/blueprints/payments.py`

**Subscription Plans:**
- Free, Go (39 CNY), Plus (129 CNY), Pro (299 CNY), Ultra (599 CNY)
- Promotional pricing available for all paid tiers
- Quota management: `backend/app/quota.py`

## Email Service

**SMTP:**
- Config: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- Default sender: `noreply@qyquant.com`
- Used for: Password reset emails
- Implementation: Flask-Mail

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry, Rollbar, etc.)

**Logs:**
- Gunicorn access/error logs to stdout
- Python standard `logging` module used throughout backend
- Celery worker logs to stdout

**Health Checks:**
- Backend: `GET /api/health` endpoint
- Frontend: Nginx root health check via `wget`
- PostgreSQL: `pg_isready` in Docker healthcheck
- Redis: `redis-cli ping` in Docker healthcheck

## CI/CD & Deployment

**Hosting:**
- Docker Compose (5 services + 1 Nginx frontend)
- Frontend served via Nginx Alpine with API reverse proxy to backend

**Nginx Configuration:**
- Location: `frontend/nginx.conf`
- SPA routing: `try_files $uri $uri/ /index.html`
- API proxy: `/api/` -> `http://backend:5000`
- Static asset caching: 1 year with immutable header
- Gzip compression enabled

**Deployment Scripts:**
- `deploy.sh` (Linux/macOS)
- `deploy.ps1` (Windows PowerShell)

**CI Pipeline:**
- None detected (no GitHub Actions, GitLab CI, etc.)

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - PostgreSQL connection string (required, app fails without it)
- `SECRET_KEY` - Flask session signing
- `JWT_SECRET` - JWT token signing
- `FERNET_KEY` - Symmetric encryption for secrets

**Optional env vars (with defaults):**
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Redis URLs for Celery
- `REDIS_URL` - Redis cache connection
- `BACKTEST_DATA_PROVIDER` - Market data source selection
- `REVIEW_AI_API_KEY`, `REVIEW_AI_BASE_URL`, `REVIEW_AI_MODEL` - AI-powered strategy review
- `E2B_API_KEY` - Remote sandbox execution
- `JQDATA_USERNAME`, `JQDATA_PASSWORD` - JoinQuant data access
- `OAUTH_WECHAT_CLIENT_ID`, `OAUTH_GITHUB_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_ID` - OAuth login
- `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` - Email sending
- `BINANCE_BASE_URL` - Binance API endpoint
- `CORS_ORIGINS` - Allowed CORS origins (default: `http://localhost:5173,http://localhost:5174`)
- `BACKEND_PORT` (default 59999), `FRONTEND_PORT` (default 58888), `POSTGRES_PORT` (default 5432), `REDIS_PORT` (default 6379)

**Secrets location:**
- `.env` file at project root (loaded by python-dotenv)
- `.env.example` present for documentation
- Docker Compose uses env var substitution with safe defaults

## Webhooks & Callbacks

**Incoming:**
- OAuth callbacks at `/api/v1/auth/oauth/callback/<provider>` (WeChat, GitHub, Google)

**Outgoing:**
- None detected (no webhook dispatch to external systems)

---

*Integration audit: 2026-04-27*
