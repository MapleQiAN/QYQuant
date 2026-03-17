<div align="center">
  <img src="frontend/src/logo.png" alt="QYQuant Logo" width="112" height="112" />

  <h1>QYQuant</h1>

  <p><strong>An integrated quant trading workspace for strategy packaging, runtime validation, market data access, and asynchronous backtesting</strong></p>

  <p>
    <a href="./README.md">中文</a>
    ·
    <a href="#quick-start">Quick Start</a>
    ·
    <a href="#core-capabilities">Highlights</a>
    ·
    <a href="#system-architecture">Architecture</a>
  </p>

  <p>
    <img alt="Vue 3" src="https://img.shields.io/badge/Vue-3.4-42b883?logo=vue.js&logoColor=white" />
    <img alt="Flask 3" src="https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white" />
    <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
    <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript&logoColor=white" />
    <img alt="Celery" src="https://img.shields.io/badge/Celery-5.3-37814A?logo=celery&logoColor=white" />
    <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white" />
    <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white" />
    <img alt="MIT License" src="https://img.shields.io/badge/License-MIT-F6C344" />
  </p>
</div>

> QYQuant currently behaves more like the kernel of a growing quant platform: the strategy workspace, backtest pipeline, market data flows, and product shell are already in place, while managed execution and richer strategy marketplace features are still evolving.

## Overview

QYQuant is a full-stack workspace for quant strategy development and operations. The repository focuses on 4 practical goals:

- standardize how strategies are packaged, imported, validated, and reused
- support both synchronous and queued backtesting workflows
- keep market data access extensible across multiple providers and cache flows
- provide a product-ready shell with dashboard, backtests, bots, forum, and settings pages

## Core Capabilities

| Area | What exists today | Notes |
| --- | --- | --- |
| Strategy workflow | Create strategies and import `.qys` / `.zip` packages | Imports validate `QYStrategy` manifests, entrypoints, and integrity declarations |
| Runtime validation | Preflight checks, parameter descriptors, runtime metadata | Designed to support future managed execution flows |
| Backtesting | `latest` synchronous backtests plus Celery job-based async backtests | Works for both dashboard previews and queued jobs |
| Market data | `auto` / Binance / FreeGold / JoinQuant-backed cache flow | Keeps room for multiple asset classes and provider strategies |
| Product console | Dashboard, Backtests, Bots, Forum, Settings | Provides a real multi-page product shell rather than isolated demos |
| Authentication | SMS-code login, JWT access token, refresh token | Development mode supports a fixed verification code |
| Internationalization | Chinese and English UI support | The Chinese project homepage lives in [README.md](./README.md) |

## Product Direction

QYQuant is not intended to stay a single-purpose tool. The broader direction is a quant platform with 3 layers:

| Layer | Goal | Current status |
| --- | --- | --- |
| Tooling | Strategy packaging, development, backtesting, metrics | Foundation exists now |
| Platform | Bot execution, quota system, account and runtime management | Partially implemented |
| Community | Strategy sharing, forum interactions, strategy distribution | Forum scaffold exists, marketplace ideas remain ahead |

That is why this README separates what is already implemented from what the product is clearly aiming toward.

## System Architecture

The diagram below reflects the flows that already exist in this repository today: a Vue 3 workspace talks to the Flask API for auth, strategy library, backtests, bots, and forum features; strategy packages are validated by `qysp` before entering storage; and backtests can run either synchronously for fast debugging or asynchronously through Celery + Redis, with market data routed to Binance, FreeGold, or the JoinQuant-backed cache path.

```mermaid
flowchart LR
    user["User / Browser"]
    cli["qys CLI / .qys Package"]

    subgraph frontend["Frontend · Vue 3"]
        web["Dashboard / Strategies / Backtests / Bots / Forum / Settings"]
        client["Router + Stores + API Client"]
    end

    subgraph backend["Backend · Flask API"]
        auth["Auth / Users"]
        strategies["Strategies Import / Runtime Metadata"]
        backtests["Backtests API"]
        community["Bots / Forum / Files"]
    end

    subgraph runtime["Execution Layer"]
        validator["qysp Validator<br/>schema + integrity"]
        engine["Backtest Engine"]
        strategyRuntime["Strategy Runtime<br/>preflight + execute"]
        worker["Celery Worker<br/>backtest queue"]
        market["Provider Router / MarketDataService"]
        report["Metrics / Report Builder"]
    end

    subgraph infra["Data & Infrastructure"]
        pg[("PostgreSQL")]
        redis[("Redis")]
        storage[("Local Storage<br/>strategies / backtest artifacts")]
        binance["Binance API"]
        freegold["FreeGold API"]
        joinquant["JoinQuant API"]
    end

    user --> web --> client
    client --> auth
    client --> strategies
    client --> backtests
    client --> community

    cli --> validator
    strategies --> validator
    strategies --> storage
    strategies --> pg

    auth --> pg
    auth --> redis
    community --> pg

    backtests -->|"GET /api/backtests/latest"| engine
    backtests -->|"POST /api/v1/backtest"| worker
    backtests --> pg

    worker <--> redis
    worker --> engine
    worker --> report
    worker --> storage
    worker --> pg

    engine --> strategyRuntime
    engine --> market
    strategyRuntime <--> storage
    strategyRuntime <--> pg

    market --> binance
    market --> freegold
    market --> joinquant
    market <--> pg
```

## Quick Start

You can run QYQuant in two ways:

- Docker one-click deployment: build the full stack with frontend, backend, PostgreSQL, Redis, and Celery.
- Developer deployment: run PostgreSQL and Redis locally, then start backend, worker, and frontend separately for iterative development.

### Option A: Docker one-click deployment

Requirements:

- Docker Engine / Docker Desktop
- Docker Compose v2

1. Clone the repository.

```bash
git clone https://github.com/MapleQiAN/QYQuant.git
cd QYQuant
```

2. Create a deployment env file.

```bash
cp .env.example .env
```

Review these values before exposing the stack outside your machine:

```env
POSTGRES_PASSWORD=qyquant_password
REDIS_PASSWORD=redis_password
SECRET_KEY=change-this-secret-key-in-production
JWT_SECRET=change-this-jwt-secret-in-production
FERNET_KEY=change-this-fernet-key-in-production
FRONTEND_PORT=58888
BACKEND_PORT=59999
CORS_ORIGINS=http://localhost:58888
AUTH_FIXED_SMS_CODE=123456
```

3. Build and start the full stack.

```bash
docker compose up -d --build
```

Optional helper scripts:

```bash
./deploy.sh
```

```powershell
.\deploy.ps1
```

Default endpoints:

- Web: [http://127.0.0.1:58888](http://127.0.0.1:58888)
- API: [http://127.0.0.1:59999](http://127.0.0.1:59999)
- Swagger UI: [http://127.0.0.1:59999/api/docs](http://127.0.0.1:59999/api/docs)

Useful operations:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker
docker compose down
```

### Option B: Developer deployment

Requirements:

| Dependency | Version |
| --- | --- |
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ |
| Redis | 7+ |
| uv | 0.4+ |

1. Clone the repository.

```bash
git clone https://github.com/MapleQiAN/QYQuant.git
cd QYQuant
```

2. Create a development env file.

```bash
cp .env.example .env.development
```

The defaults in `.env.example` already match the root Compose dependency stack:

```env
DATABASE_URL=postgresql://qyquant:qyquant_password@localhost:5432/qyquant
REDIS_URL=redis://:redis_password@localhost:6379/0
CELERY_BROKER_URL=redis://:redis_password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:redis_password@localhost:6379/1
SECRET_KEY=change-this-secret-key-in-production
JWT_SECRET=change-this-jwt-secret-in-production
FERNET_KEY=change-this-fernet-key-in-production
CORS_ORIGINS=http://localhost:58888
AUTH_FIXED_SMS_CODE=123456
```

If you want JoinQuant-backed data, also set:

```env
JQDATA_USERNAME=your-account
JQDATA_PASSWORD=your-password
```

3. Start PostgreSQL and Redis.

```bash
docker compose up -d postgres redis
```

4. Install Python dependencies.

```bash
uv sync --dev
```

5. Initialize the database.

```bash
uv run --package qyquant-backend flask --app app db upgrade
```

6. Start the backend.

```bash
uv run --package qyquant-backend flask --app app run --debug --port 59999
```

After that:

- API: [http://127.0.0.1:59999](http://127.0.0.1:59999)
- Swagger UI: [http://127.0.0.1:59999/api/docs](http://127.0.0.1:59999/api/docs)

7. Start the Celery worker.

```bash
uv run --package qyquant-backend celery -A app.celery_app worker --loglevel=info
```

If you also need scheduled jobs:

```bash
uv run --package qyquant-backend celery -A app.celery_app beat --loglevel=info
```

8. Start the frontend.

```bash
cd frontend
npm install
npm run dev
```

Default address:

- Web: [http://127.0.0.1:58888](http://127.0.0.1:58888)

> The Vite dev server proxies `/api` to `http://127.0.0.1:59999`.

## Developer Notes

### Authentication flow

This repository no longer uses the old default admin account described by earlier versions of the README. The current login flow is:

1. `POST /api/v1/auth/send-code`
2. `POST /api/v1/auth/login`
3. Use the returned `access_token` in the frontend

When `AUTH_FIXED_SMS_CODE` is configured, local integration becomes much easier.

### Key API routes

| Module | Key routes |
| --- | --- |
| Health | `GET /api/health` |
| Auth | `POST /api/v1/auth/send-code`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` |
| Users | `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me` |
| Strategies | `POST /api/strategies`, `POST /api/strategies/import`, `GET /api/strategies/recent`, `GET /api/strategies/<strategy_id>/runtime` |
| Backtests | `POST /api/backtests/run`, `GET /api/backtests/job/<job_id>`, `GET /api/backtests/latest`, `GET /api/v1/backtest/quota`, `GET /api/v1/backtest/<job_id>`, `POST /api/v1/backtest/` |
| Bots | `GET /api/bots/recent`, `POST /api/bots`, `PATCH /api/bots/<bot_id>/status`, `GET /api/bots/<bot_id>/performance` |
| Forum | `GET /api/forum/hot`, `POST /api/forum/posts` |

### Strategy package format

When importing a strategy package, the backend validates:

- `strategy.json` must exist
- `schemaVersion` must be `1.0`
- `kind` must be `QYStrategy`
- `runtime.name` and `runtime.version` must exist
- `entrypoint.path` and `entrypoint.callable` must exist
- if `integrity.files` is declared, file size and hash values are verified

The repository also ships `packages/qysp`, which exposes the `qys` CLI after installation.

## Project Structure

```text
QYQuant/
|- frontend/               # Vue 3 frontend
|- backend/                # Flask API, backtests, tasks, runtime
|- packages/qysp/          # Strategy package tooling and CLI
|- docs/                   # Project docs
|- .gitnexus/              # GitNexus index metadata
|- .env.example            # Environment template
|- docker-compose.yml      # Containerized dependencies and deployment orchestration
```

## Roadmap

### Already in the repository

- [x] Strategy creation and package import
- [x] Backtest job pipeline
- [x] Multi-page product console
- [x] Basic bot and forum APIs
- [x] Bilingual frontend and generated API docs

### Worth building next

- [ ] richer managed execution and account binding flows
- [ ] more complete backtest result views and metrics
- [ ] stronger strategy sharing and marketplace experiences
- [ ] clearer quota, subscription, and monetization model
- [ ] better real-time data and push flows

## Testing

Backend:

```bash
uv run pytest backend/tests -q
```

Frontend:

```bash
cd frontend
npm test
```

## Contributing

Issues and pull requests are welcome. Before opening a larger change, it helps to document the intended scope and direction first.

Suggested pre-submit checks:

```bash
uv run pytest backend/tests -q
cd frontend && npm test
```

## License

This project is licensed under the MIT License.
