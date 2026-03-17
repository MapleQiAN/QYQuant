<div align="center">
  <img src="frontend/src/logo.png" alt="QYQuant Logo" width="112" height="112" />

  <h1>QYQuant</h1>

  <p><strong>策略包导入、运行时校验、市场数据接入与异步回测的一体化量化交易工作台</strong></p>

  <p>
    <a href="./README.en.md">English</a>
    ·
    <a href="#快速开始">Quick Start</a>
    ·
    <a href="#核心能力">Highlights</a>
    ·
    <a href="#项目结构">Architecture</a>
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

> QYQuant 当前更接近一个正在成形的量化平台内核：策略工作台、回测链路、市场数据与产品化控制台已经落地；更完整的托管执行、策略分享和市场能力仍在持续演进。

## 项目简介

QYQuant 是一个面向量化策略研发与运营的全栈工作台，前端使用 Vue 3，后端使用 Flask。当前仓库重点解决 4 件事：

- 让策略可以被标准化打包、导入、校验和复用
- 让回测既能同步查看结果，也能通过 Celery 异步排队执行
- 让市场数据接入具备可扩展性，支持多数据源和缓存链路
- 让产品界面具备仪表盘、回测、机器人、论坛、设置等完整产品壳

## 核心能力

| 能力域 | 当前已实现 | 说明 |
| --- | --- | --- |
| 策略工作流 | 新建策略、导入 `.qys` / `.zip` 策略包 | 导入时会校验 `QYStrategy` 清单、入口文件和完整性声明 |
| 运行时校验 | 运行前预检查、参数描述、运行时元信息读取 | 面向后续策略托管和执行链路 |
| 回测系统 | `latest` 同步回测 + Celery 异步任务回测 | 既适合仪表盘展示，也支持更正式的任务流 |
| 市场数据 | `auto` / Binance / FreeGold / JoinQuant 缓存链路 | 为不同资产和数据质量场景预留扩展空间 |
| 产品控制台 | Dashboard、Backtests、Bots、Forum、Settings | 已具备开箱可用的多页面产品骨架 |
| 用户与认证 | 短信验证码登录、JWT 访问令牌、刷新令牌 | 开发环境支持固定验证码联调 |
| 国际化 | 中文 / English 双语界面 | 英文说明见 [README.en.md](./README.en.md) |

## 产品方向

QYQuant 的长期方向不是单点工具，而是一个由 3 个层次构成的量化平台：

| 层次 | 目标 | 当前状态 |
| --- | --- | --- |
| Tooling | 策略开发、打包、回测、指标查看 | 已有基础能力 |
| Platform | 机器人运行、配额体系、账户与执行托管 | 部分能力已落地，仍在完善 |
| Community | 策略分享、论坛互动、内容与策略分发 | 论坛骨架已在仓库中，市场化能力待推进 |

这也是 README 的组织方式：既展示现在能跑起来的部分，也保留项目为何值得继续投入的方向感。

## 快速开始

### 环境要求

| 依赖 | 版本 |
| --- | --- |
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ |
| Redis | 7+ |
| uv | 0.4+ |

### 1. 克隆仓库

```bash
git clone https://github.com/MapleQiAN/QYQuant.git
cd QYQuant
```

### 2. 配置环境变量

复制根目录模板：

```bash
cp .env.example .env.development
```

至少确认以下配置存在且可用：

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/qyquant
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-this-jwt-secret-in-production
SECRET_KEY=change-this-secret-key-in-production
FERNET_KEY=change-this-fernet-key-in-production
CORS_ORIGINS=http://localhost:58888
```

开发环境如果不想接真实短信，可以加上：

```env
AUTH_FIXED_SMS_CODE=123456
```

如果需要 JoinQuant 数据，再补充：

```env
JQDATA_USERNAME=your-account
JQDATA_PASSWORD=your-password
```

### 3. 启动 PostgreSQL 与 Redis

如果本机没有现成服务，可以直接用根目录 Compose 启动依赖：

```bash
docker compose up -d postgres redis
```

### 4. 安装 Python 依赖

推荐在仓库根目录使用 `uv`，这样会同时安装 `backend` 和本地包 `packages/qysp`：

```bash
uv sync --dev
```

### 5. 初始化数据库

```bash
uv run --package qyquant-backend flask --app app db upgrade
```

### 6. 启动后端

```bash
uv run --package qyquant-backend flask --app app run --debug --port 59999
```

启动后可访问：

- API: [http://127.0.0.1:59999](http://127.0.0.1:59999)
- Swagger UI: [http://127.0.0.1:59999/api/docs](http://127.0.0.1:59999/api/docs)

### 7. 启动 Celery Worker

异步回测依赖 Redis 与 Celery Worker：

```bash
uv run --package qyquant-backend celery -A app.celery_app worker --loglevel=info
```

如需定时任务，可额外启动：

```bash
uv run --package qyquant-backend celery -A app.celery_app beat --loglevel=info
```

### 8. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

- Web: [http://127.0.0.1:58888](http://127.0.0.1:58888)

> 当前前端开发代理会把 `/api` 请求转发到 `http://127.0.0.1:59999`。

## 开发者提示

### 认证方式

当前仓库不再使用旧版 README 中的默认管理员账号。登录流程是：

1. `POST /api/v1/auth/send-code` 发送验证码
2. `POST /api/v1/auth/login` 使用手机号 + 验证码登录
3. 前端使用返回的 `access_token`

如果配置了 `AUTH_FIXED_SMS_CODE`，本地联调时可以直接使用固定验证码。

### 主要接口

| 模块 | 关键接口 |
| --- | --- |
| Health | `GET /api/health` |
| Auth | `POST /api/v1/auth/send-code`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` |
| Users | `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me` |
| Strategies | `POST /api/strategies`, `POST /api/strategies/import`, `GET /api/strategies/recent`, `GET /api/strategies/<strategy_id>/runtime` |
| Backtests | `POST /api/backtests/run`, `GET /api/backtests/job/<job_id>`, `GET /api/backtests/latest`, `GET /api/v1/backtest/quota`, `GET /api/v1/backtest/<job_id>`, `POST /api/v1/backtest/` |
| Bots | `GET /api/bots/recent`, `POST /api/bots`, `PATCH /api/bots/<bot_id>/status`, `GET /api/bots/<bot_id>/performance` |
| Forum | `GET /api/forum/hot`, `POST /api/forum/posts` |

### 策略包格式

导入策略包时，后端会校验：

- 必须包含 `strategy.json`
- `schemaVersion` 必须是 `1.0`
- `kind` 必须是 `QYStrategy`
- `runtime.name` 与 `runtime.version` 必须存在
- `entrypoint.path` 与 `entrypoint.callable` 必须存在
- 若声明 `integrity.files`，则会校验文件大小和哈希

仓库中的 `packages/qysp` 提供了相关工具，安装后可使用 `qys` CLI。

## 项目结构

```text
QYQuant/
|- frontend/               # Vue 3 前端应用
|- backend/                # Flask API、回测、任务、运行时
|- packages/qysp/          # 策略包工具与 CLI
|- docs/                   # 项目文档
|- .gitnexus/              # GitNexus 索引与元数据
|- .env.example            # 环境变量模板
|- docker-compose.yml      # 容器化依赖与部署编排
```

## Roadmap

### 现在已经有

- [x] 策略创建与包导入
- [x] 回测任务链路
- [x] 多页产品控制台
- [x] 论坛与机器人基础接口
- [x] 双语前端与 API 文档

### 接下来更值得做的

- [ ] 更完整的策略托管执行与账户绑定
- [ ] 更细致的回测结果与指标展示
- [ ] 更成熟的策略分享与市场化分发
- [ ] 更明确的订阅、配额与增长模型
- [ ] 更强的实时数据与推送能力

## 测试

后端：

```bash
uv run pytest backend/tests -q
```

前端：

```bash
cd frontend
npm test
```

## Contributing

欢迎提交 Issue 和 Pull Request。建议在提交前至少完成以下检查：

```bash
uv run pytest backend/tests -q
cd frontend && npm test
```

如果你要做较大的功能改动，建议先在 Issue 或文档中说明意图和范围，再进入实现阶段。

## License

This project is licensed under the MIT License.
