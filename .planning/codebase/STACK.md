# Technology Stack

**Analysis Date:** 2026-04-27

## Languages

**Primary:**
- Python 3.11 - Backend API, strategy execution, data processing, task workers
- TypeScript / JavaScript (ES2020) - Frontend SPA

**Secondary:**
- SQL (PostgreSQL dialect) - Database migrations and queries via SQLAlchemy
- Mako templates - Alembic migration script generation

## Runtime

**Environment:**
- Python 3.11 (slim-bookworm Docker base image)
- Node.js 20 (Alpine Docker base image for frontend build)

**Package Manager:**
- **Backend:** uv (workspace-based monorepo)
  - Lockfile: `uv.lock` (present)
  - Workspace members: `packages/qysp`, `backend`
  - pip used inside Docker containers (via `requirements.txt`)
- **Frontend:** npm (with `package-lock.json` present)
  - Secondary: `pnpm-lock.yaml` also present

## Frameworks

**Core:**
- Flask 3.0.x - Backend REST API server
- Vue 3.4.x - Frontend SPA framework
- Vite 5.x - Frontend build tool and dev server

**Flask Extensions:**
- flask-sqlalchemy 3.1.1 - ORM and database layer
- flask-migrate 4.0.7 - Alembic-based database migrations
- flask-jwt-extended 4.6.0 - JWT authentication
- flask-cors 4.0.x - CORS handling
- flask-smorest 0.44.0 - OpenAPI / REST API scaffolding
- flask-mail 0.10.x - Email sending

**Frontend Libraries:**
- vue-router 4.3.x - Client-side routing
- Pinia 2.1.x - State management
- vue-i18n 11.x - Internationalization
- axios 1.7.x - HTTP client
- ECharts 6.x - Charting and data visualization
- Monaco Editor 0.55.x - Code editor (strategy editing)
- vue-toastification 2.x - Toast notifications
- DOMPurify 3.4.x - HTML sanitization
- marked 18.x - Markdown rendering

**Testing:**
- pytest 7.4.4 - Backend test runner
- pytest-flask 1.3.0 - Flask test utilities
- pytest-cov 6.0+ - Coverage reporting
- Vitest 1.6.x - Frontend test runner
- @vue/test-utils 2.4.x - Vue component testing
- jsdom 24.x - DOM simulation
- MSW 2.2.x - API mocking for frontend tests

**Build/Dev:**
- Gunicorn 23.0.0 - Production WSGI server
- vue-tsc 3.2.x - Vue TypeScript checking
- Ruff 0.4+ - Python linter/formatter (dev dependency)
- Hatchling - Python build backend for workspace packages

## Key Dependencies

**Critical:**
- SQLAlchemy (via flask-sqlalchemy) - ORM, migration, query building
- Celery 5.3.6 - Distributed task queue (backtest execution, notifications, scheduled jobs)
- redis 5.0.6 - Celery broker, caching, auth token store
- psycopg[binary] 3.1.18 / psycopg2-binary 2.9.9 - PostgreSQL drivers (dual driver setup)
- cryptography 42.0.8 - Fernet encryption for secrets and strategy code
- marshmallow 3.21.2 - Schema validation and serialization
- authlib 1.3+ - OAuth client for third-party login

**Financial Data:**
- akshare 1.18+ - Chinese A-share market data (stocks, futures, funds)
- jqdatasdk 1.9+ - JoinQuant financial data API

**AI/Code Execution:**
- openai-agents 0.14+ - AI agent framework
- e2b-code-interpreter 1.5+ - E2B sandbox for strategy code execution

**Content Moderation:**
- pyahocorasick 2.0+ - Aho-Corasick automaton for sensitive word matching

**Internal Package:**
- qysp (workspace package) - Quant strategy package with CLI (`qys` command), schema validation, indicator support, and template system
  - Location: `packages/qysp/`
  - Entry point: `qysp.cli.main:cli`

## Configuration

**Environment:**
- Dotenv-based configuration (`python-dotenv 1.0.1`)
- Environment-specific files: `.env.{FLASK_ENV}` or `.env`
- Config class hierarchy: `BaseConfig` -> `DevConfig` / `TestConfig` / `ProdConfig`
- Config file: `backend/app/config.py`

**Build:**
- `pyproject.toml` - Workspace root, backend, and qysp package configs
- `backend/requirements.txt` - Docker container dependency pinning
- `frontend/vite.config.js` - Vite build configuration with Monaco chunk splitting
- `frontend/tsconfig.json` - TypeScript strict mode, ES2020 target, path alias `@/*`

## Platform Requirements

**Development:**
- Python >=3.11
- Node.js 20+
- PostgreSQL 15+ (via Docker or local)
- Redis 7+ (via Docker or local)
- uv package manager

**Production:**
- Docker Compose orchestration
- 5 containers: postgres, redis, backend, celery-worker, celery-beat, frontend (Nginx)
- PostgreSQL 15 Alpine for data persistence
- Redis 7 Alpine for caching and task queue
- Gunicorn with configurable workers (default 4) and timeout (default 120s)
- Nginx Alpine serving frontend static files with API reverse proxy

---

*Stack analysis: 2026-04-27*
