# QYQuant

QYQuant is a quantitative trading workspace with a Vue 3 frontend and a Flask backend. The current codebase focuses on strategy package import, runtime validation, market data access, asynchronous backtesting, and a dashboard-oriented product shell.

## 中文

### 当前能力

- 策略创建与导入：支持直接创建策略，或导入 `.qys` / `.zip` 策略包。
- 策略运行时校验：校验 `QYStrategy` 清单、入口文件、参数描述和归档完整性。
- 回测能力：支持同步获取最新回测结果，也支持 Celery 异步回测任务。
- 市场数据：支持 `auto` / Binance / FreeGold 数据源，并提供 JoinQuant 日线缓存服务。
- 产品界面：包含仪表盘、策略新建、回测、机器人、论坛、设置等页面。
- 用户体系：基于短信验证码登录、JWT 访问令牌和刷新令牌。
- 国际化：前端内置 `zh` / `en` 两套文案。

### 技术栈

- 前端：Vue 3, TypeScript, Vite, Pinia, Vue Router, Vue I18n, ECharts, Vitest
- 后端：Flask, Flask-Smorest, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Celery
- 数据层：PostgreSQL, Redis
- Python 工作区：`uv` workspace + 本地包 `packages/qysp`

### 目录结构

```text
QYQuant/
|- frontend/               # Vue 3 前端
|- backend/                # Flask API、回测、任务、运行时
|- packages/qysp/          # 策略包工具与 CLI
|- docs/                   # 项目文档
|- .env.example            # 环境变量模板
|- docker-compose.yml      # 容器化部署编排
```

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- `uv` 0.4+

### 本地开发

#### 1. 克隆仓库

```bash
git clone https://github.com/MapleQiAN/QYQuant.git
cd QYQuant
```

#### 2. 配置环境变量

复制根目录环境变量模板并按需修改：

```bash
cp .env.example .env.development
```

至少确认以下配置有效：

- `DATABASE_URL`
- `REDIS_URL`
- `CORS_ORIGINS`
- `JWT_SECRET`
- `SECRET_KEY`
- `FERNET_KEY`

开发环境如果不想接真实短信，可以设置固定验证码：

```env
AUTH_FIXED_SMS_CODE=123456
```

如需 JoinQuant 数据，请补充：

```env
JQDATA_USERNAME=your-account
JQDATA_PASSWORD=your-password
```

#### 3. 启动 PostgreSQL 和 Redis

如果本机未安装，可直接使用仓库根目录的 Compose 启动依赖：

```bash
docker compose up -d postgres redis
```

#### 4. 安装 Python 依赖

推荐在仓库根目录使用 `uv`，这样会同时安装 `backend` 与 `packages/qysp`：

```bash
uv sync --dev
```

#### 5. 初始化数据库

```bash
uv run --package qyquant-backend flask --app app db upgrade
```

#### 6. 启动后端

```bash
uv run --package qyquant-backend flask --app app run --debug --port 59999
```

后端默认地址：

- API: [http://127.0.0.1:59999](http://127.0.0.1:59999)
- Swagger: [http://127.0.0.1:59999/api/docs](http://127.0.0.1:59999/api/docs)

#### 7. 启动 Celery Worker

异步回测依赖 Redis 和 Celery Worker：

```bash
uv run --package qyquant-backend celery -A app.celery_app worker --loglevel=info
```

如需定时任务，可额外启动：

```bash
uv run --package qyquant-backend celery -A app.celery_app beat --loglevel=info
```

#### 8. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

- Web: [http://127.0.0.1:58888](http://127.0.0.1:58888)

当前 Vite 开发代理会把 `/api` 请求转发到 `http://127.0.0.1:59999`。

### 认证说明

当前仓库不再使用 README 旧版里的默认管理员账号。登录流程为：

1. `POST /api/v1/auth/send-code` 发送验证码
2. `POST /api/v1/auth/login` 使用手机号 + 验证码登录
3. 前端使用返回的 `access_token`

本地开发若配置了 `AUTH_FIXED_SMS_CODE`，可直接使用固定验证码联调。

### 主要接口

#### 健康检查

- `GET /api/health`

#### 认证

- `POST /api/v1/auth/send-code`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

#### 用户

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `DELETE /api/v1/users/me`

#### 策略

- `POST /api/strategies`
- `POST /api/strategies/import`
- `GET /api/strategies/recent`
- `GET /api/strategies/<strategy_id>/runtime`

#### 回测

- `POST /api/backtests/run`
- `GET /api/backtests/job/<job_id>`
- `GET /api/backtests/latest`
- `GET /api/v1/backtest/quota`
- `GET /api/v1/backtest/<job_id>`
- `POST /api/v1/backtest/`

#### 机器人与论坛

- `GET /api/bots/recent`
- `POST /api/bots`
- `PATCH /api/bots/<bot_id>/status`
- `GET /api/bots/<bot_id>/performance`
- `GET /api/forum/hot`
- `POST /api/forum/posts`

### 策略包格式

导入策略包时，后端会校验以下内容：

- 必须包含 `strategy.json`
- `schemaVersion` 必须为 `1.0`
- `kind` 必须为 `QYStrategy`
- `runtime.name` / `runtime.version` 必须存在
- `entrypoint.path` / `entrypoint.callable` 必须存在
- 如声明 `integrity.files`，则会校验文件哈希与大小

仓库内的 `packages/qysp` 提供了策略包相关工具，安装后可使用 `qys` CLI。

### 测试

后端：

```bash
uv run pytest backend/tests -q
```

前端：

```bash
cd frontend
npm test
```

## English

### Overview

QYQuant is a full-stack quantitative trading workspace built with Vue 3 and Flask. The current implementation centers on strategy package import, runtime validation, market data integration, asynchronous backtests, and a dashboard-style frontend.

### Highlights

- Create strategies or import `.qys` / `.zip` packages
- Validate `QYStrategy` manifests and runtime entrypoints
- Run latest backtests synchronously or queue asynchronous Celery jobs
- Use market data from auto selection, Binance, FreeGold, and JoinQuant-backed cache flows
- Work with dashboard, bots, forum, and settings pages
- Authenticate with SMS code login plus JWT access and refresh tokens

### Local Development

1. Copy `.env.example` to `.env.development`
2. Start PostgreSQL and Redis with `docker compose up -d postgres redis`
3. Install Python dependencies with `uv sync --dev`
4. Run migrations with `uv run --package qyquant-backend flask --app app db upgrade`
5. Start backend on port `59999`
6. Start frontend in `frontend/` with `npm install && npm run dev`
7. Open [http://127.0.0.1:58888](http://127.0.0.1:58888)

Swagger UI is available at [http://127.0.0.1:59999/api/docs](http://127.0.0.1:59999/api/docs).

## License

This project is licensed under the MIT License.
