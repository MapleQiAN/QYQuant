<div align="center">

<img src="frontend/src/logo.png" alt="QYQuant Logo" width="120" height="120"/>

# QYQuant 量化交易平台

**专业的数字货币量化交易回测与模拟交易平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue 3](https://img.shields.io/badge/Vue-3.4-42b883?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [API 文档](#-api-文档) • [开发指南](#-开发指南)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 📖 项目简介

QYQuant 是一个全栈量化交易平台，提供策略回测、模拟交易、社区交流等核心功能。采用前后端分离架构，支持中英文双语界面。

### ✨ 功能特性

#### 核心功能

| 功能 | 描述 |
|:---:|:---|
| 🎯 **策略管理** | 创建、编辑、版本控制交易策略 |
| 📈 **历史回测** | 基于 Celery 异步任务的高性能回测引擎 |
| 🤖 **模拟交易** | 纸面交易机器人，实时监控策略表现 |
| 💬 **社区论坛** | 策略分享、评论、点赞、打赏功能 |
| 📁 **文件管理** | 策略文件上传下载，支持版本管理 |
| 🔐 **用户系统** | JWT 认证、用户资料、关注功能 |

#### 技术亮点

<div align="center">

![Vue](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vue.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Pinia](https://img.shields.io/badge/Pinia-Store-ffcd69?style=for-the-badge&logo=pinia&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)

</div>

- 🎨 **现代化 UI** - Vue 3 组合式 API + TypeScript
- 🌍 **国际化** - 内置中英文双语支持
- 📊 **响应式设计** - 完美适配桌面端和移动端
- 🔐 **安全认证** - JWT Token + 加密存储
- ⚡ **异步任务** - Celery + Redis 任务队列
- 🗄️ **数据持久化** - PostgreSQL + SQLAlchemy ORM
- 🧪 **完善测试** - Vitest (前端) + Pytest (后端)

---

## 🚀 快速开始

### 📋 环境要求

| 依赖 | 版本要求 | 图标 |
|------|---------|------|
| Node.js | 18+ (推荐 18/20) | ![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white) |
| Python | 3.10+ | ![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white) |
| npm | 最新版 | ![npm](https://img.shields.io/badge/npm-latest-CB3837?logo=npm&logoColor=white) |
| Docker | (可选，用于数据库服务) | ![Docker](https://img.shields.io/badge/Docker-Optional-2496ED?logo=docker&logoColor=white) |

### 📥 1. 克隆项目

```bash
git clone https://github.com/MapleQiAN/QYQuant.git
cd QYQuant
```

### 🐳 方式一：Docker 一键部署（推荐）

<div align="center">

![Docker](https://img.shields.io/badge/Docker-支持-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-支持-2496ED?style=for-the-badge&logo=docker&logoColor=white)

一键部署全部服务：前端 + 后端 + 数据库 + Redis + Celery

</div>

#### 🎯 快速启动

**Linux / macOS:**

```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows (PowerShell):**

```powershell
.\deploy.ps1
```

#### 🛠️ 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改密码和密钥配置

# 2. 启动所有服务（前端、后端、数据库、Redis、Celery）
docker compose up -d

# 3. 初始化数据库（可选）
docker compose exec backend flask db upgrade

# 4. 查看服务状态
docker compose ps

# 5. 查看日志
docker compose logs -f
```

#### 📊 服务说明

Docker 部署包含以下服务：

| 服务 | 描述 | 端口 |
|:---:|:-----|:-----|
| **frontend** | Vue 3 前端应用 (Nginx) | 80 |
| **backend** | Flask API 服务 (Gunicorn) | 5000 |
| **celery-worker** | Celery 异步任务处理 | - |
| **celery-beat** | Celery 定时任务调度 | - |
| **postgres** | PostgreSQL 数据库 | 5432 |
| **redis** | Redis 缓存和消息队列 | 6379 |

<div align="center">

**🌐 访问地址**: `http://localhost`

**🔑 默认账号**: `admin / admin123`

</div>

#### 📝 常用命令

```bash
# 停止所有服务
docker compose down

# 重启服务
docker compose restart

# 重新构建镜像
docker compose build --no-cache

# 查看服务日志
docker compose logs -f [服务名]

# 进入容器
docker compose exec backend bash
docker compose exec postgres psql -U qyquant -d qyquant

# 清理数据（谨慎操作）
docker compose down -v  # 删除所有数据卷
```

#### 🔧 生产环境部署建议

1. **修改默认密码**：编辑 `.env` 文件，修改所有密码和密钥
2. **配置 HTTPS**：使用 Nginx 反向代理 + Let's Encrypt 证书
3. **数据备份**：定期备份 PostgreSQL 数据卷
4. **资源限制**：根据服务器配置调整 `docker-compose.yml` 中的资源限制
5. **日志管理**：配置日志轮转，避免磁盘占满

---

### 💻 方式二：本地部署（不使用 Docker）

<div align="center">

![Node.js](https://img.shields.io/badge/本地部署-完整指南-339933?style=for-the-badge&logo=none)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-手动安装-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-手动安装-DC382D?style=for-the-badge&logo=redis&logoColor=white)

适用于需要完全控制本地开发环境的开发者

</div>

#### 📦 第一步：安装系统依赖

**1. 安装 PostgreSQL 15+**

- **Windows**：从 [PostgreSQL 官网](https://www.postgresql.org/download/windows/) 下载安装
- **macOS**：`brew install postgresql@15`
- **Linux (Ubuntu/Debian)**：
  ```bash
  sudo apt update
  sudo apt install postgresql postgresql-contrib
  sudo systemctl start postgresql
  ```

**2. 安装 Redis 7+**

- **Windows**：
  - 推荐：使用 WSL2 安装 Linux 版 Redis
  - 或下载 [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- **macOS**：`brew install redis`
- **Linux (Ubuntu/Debian)**：
  ```bash
  sudo apt install redis-server
  sudo systemctl start redis
  ```

**3. 验证安装**

```bash
# 检查 PostgreSQL
psql --version

# 检查 Redis
redis-cli ping  # 应返回 PONG
```

#### 🗄️ 第二步：配置数据库

**1. 创建数据库和用户**

```bash
# 连接到 PostgreSQL
psql -U postgres

# 在 PostgreSQL 命令行中执行：
CREATE DATABASE qyquant;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE qyquant TO postgres;
\q
```

**2. 验证连接**

```bash
psql -U postgres -d qyquant -c "SELECT version();"
```

#### 🔧 第三步：配置后端环境

**1. 进入后端目录**

```bash
cd backend
```

**2. 配置环境变量**

编辑 `.env.development` 文件（或从 `.env.example` 复制）：

```env
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qyquant
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-key
FERNET_KEY=your-fernet-key
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
BACKTEST_DATA_PROVIDER=binance
BINANCE_BASE_URL=https://api.binance.com
```

**3. 创建 Python 虚拟环境**

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

**4. 安装 Python 依赖**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**5. 初始化数据库**

```bash
# 运行数据库迁移
flask db upgrade

# 创建默认管理员账号（可选）
python scripts/seed.py
```

<div align="center">

**🔑 默认账号**: `admin / admin123`

</div>

**6. 启动后端服务**

```bash
# 启动 Flask 开发服务器
flask --app app run
```

后端将在 `http://127.0.0.1:5000` 启动。

**7. 启动 Celery Worker（可选，用于异步任务）**

```bash
# 终端 1：启动 Celery Worker
celery -A app.celery_app worker --loglevel=info

# 终端 2（可选）：启动 Celery Beat 定时任务
celery -A app.celery_app beat --loglevel=info
```

#### 🎨 第四步：启动前端服务

**1. 进入前端目录**

```bash
cd frontend
```

**2. 安装 Node.js 依赖**

```bash
npm install
```

**3. 配置环境变量**

创建 `.env.development` 文件：

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

**4. 启动前端开发服务器**

```bash
npm run dev
```

前端将在 `http://127.0.0.1:5173` 启动。

#### 🎉 第五步：访问应用

打开浏览器访问 [http://127.0.0.1:5173](http://127.0.0.1:5173)

<div align="center">

| 服务 | 地址 | 说明 |
|:---:|:-----|:-----|
| **前端应用** | http://127.0.0.1:5173 | Vue 3 开发服务器 |
| **后端 API** | http://127.0.0.1:5000 | Flask 开发服务器 |
| **API 文档** | http://127.0.0.1:5000/api/docs | Swagger UI |

</div>

#### 🔍 故障排除

**PostgreSQL 连接失败**

```bash
# 检查 PostgreSQL 服务状态
# Linux
sudo systemctl status postgresql

# macOS
brew services list

# Windows
# 检查服务中的 PostgreSQL 服务
```

**Redis 连接失败**

```bash
# 检查 Redis 服务状态
# Linux
sudo systemctl status redis

# macOS
brew services list

# 启动 Redis
redis-server
```

**端口被占用**

```bash
# 查看端口占用情况
# Windows
netstat -ano | findstr :5000
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Linux/macOS
lsof -i :5000
lsof -i :5432
lsof -i :6379
```

**Python 依赖安装失败**

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源（可选）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 📝 开发提示

- **热重载**：Flask 和 Vite 都支持热重载，修改代码后会自动重启
- **调试模式**：开发模式下 Flask 会显示详细错误信息
- **日志查看**：后端日志会在终端直接输出
- **数据库管理**：可使用 pgAdmin、DBeaver 等 GUI 工具管理 PostgreSQL

---

### 🔧 2. 启动后端服务

#### 方式一：使用 Docker (推荐)

```bash
cd backend
docker compose up -d  # 启动 PostgreSQL + Redis
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
flask --app app run
```

#### 方式二：本地数据库

修改 `backend/.env.development` 中的数据库配置，然后运行：

```bash
cd backend
pip install -r requirements.txt
flask --app app run
```

<div align="center">

**🌐 后端地址**: `http://127.0.0.1:5000`

**🔑 默认账号**: `admin / admin123` (运行 `python scripts/seed.py` 创建)

</div>

### 🎨 3. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

<div align="center">

**🌐 前端地址**: `http://127.0.0.1:5173`

</div>

### 🎉 4. 访问应用

打开浏览器访问 `http://127.0.0.1:5173`，开始使用 QYQuant！

---

## 🏗️ 技术架构

### 📱 前端技术栈

```text
Vue 3 + Vite
├── 🎨 UI 框架: Vue 3 Composition API
├── 🔷 类型系统: TypeScript 5.3
├── 📦 状态管理: Pinia
├── 🛣️ 路由管理: Vue Router 4
├── 🌐 HTTP 客户端: Axios
├── 🌍 国际化: Vue I18n
├── 🔔 通知提示: Vue Toastification
├── ⚡ 构建工具: Vite 5
├── 🧪 测试框架: Vitest + Vue Test Utils
└── 🎭 Mock 服务: MSW (开发中)
```

### 🔧 后端技术栈

```text
Flask + Python 3.10+
├── 🌐 Web 框架: Flask 3.0
├── 🗄️ ORM: SQLAlchemy
├── 🔄 数据库迁移: Alembic (Flask-Migrate)
├── 📚 API 文档: Flask-Smorest (OpenAPI 3.0)
├── 🔐 认证授权: Flask-JWT-Extended
├── ⚙️ 异步任务: Celery 5.3
├── 🔴 缓存队列: Redis 7
├── 🐘 数据库: PostgreSQL 15
├── 🔒 加密库: Cryptography (Fernet)
└── 🧪 测试框架: Pytest + Pytest-Flask
```

### 📂 项目结构

```text
QYQuant/
├── 📁 frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── 📡 api/             # API 客户端
│   │   ├── 🎨 components/      # Vue 组件
│   │   ├── 📦 stores/          # Pinia 状态管理
│   │   ├── 👁️ views/           # 页面视图
│   │   ├── 🔷 types/           # TypeScript 类型
│   │   ├── 🌍 i18n/            # 国际化配置
│   │   └── 🛣️ router/          # 路由配置
│   ├── 📦 package.json
│   └── ⚙️ vite.config.ts
│
├── 📁 backend/                 # Flask 后端 API
│   ├── app/
│   │   ├── 📋 blueprints/      # API 蓝图模块
│   │   ├── 🗃️ models/          # 数据模型
│   │   ├── 📄 schemas/         # Marshmallow 序列化
│   │   ├── 📊 backtest/        # 回测引擎
│   │   ├── ⚙️ tasks/           # Celery 任务
│   │   ├── 🛠️ utils/           # 工具函数
│   │   ├── ⚙️ config.py        # 配置管理
│   │   └── 🔌 extensions.py    # Flask 扩展
│   ├── 🔄 migrations/          # 数据库迁移
│   ├── 🧪 tests/               # 后端测试
│   ├── 📜 scripts/             # 脚本工具
│   ├── 📦 requirements.txt
│   └── 🐳 docker-compose.yml
│
└── 📁 docs/                    # 项目文档
    ├── 📄 api-contract.md
    └── 📋 plans/               # 设计文档
```

---

## 📡 API 文档

### 🌐 基础信息

<div align="center">

**Base URL**: `/api`

**认证方式**: 🔑 JWT Bearer Token

**响应格式**: 📦 统一信封格式

</div>

### ✅ 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": { /* 业务数据 */ },
  "request_id": "uuid"
}
```

### ❌ 错误响应

```json
{
  "code": "40001",
  "message": "参数验证失败",
  "details": { /* 详细信息 */ }
}
```

### 🔌 核心接口

#### 🔐 认证模块 `/api/auth`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| POST | `/login` | 用户登录，返回 access_token |

#### 👤 用户模块 `/api/users`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| GET | `/me` | 获取当前用户信息 |

#### 📊 策略模块 `/api/strategies`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| GET | `/recent` | 获取最近策略列表 |

#### 📈 回测模块 `/api/backtests`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| POST | `/run` | 创建回测任务，返回 job_id |
| GET | `/job/<job_id>` | 查询任务状态和结果 |
| GET | `/latest` | 获取最新回测概览 |

#### 🤖 机器人模块 `/api/bots`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| GET | `/recent` | 获取最近运行的机器人 |
| POST | `/` | 创建新的机器人实例 |
| PATCH | `/<id>/status` | 更新机器人运行状态 |
| GET | `/<id>/performance` | 获取机器人绩效数据 |

#### 💬 论坛模块 `/api/forum`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| GET | `/hot` | 获取热门帖子 |
| POST | `/posts` | 创建新帖子 |
| POST | `/posts/<id>/comments` | 发表评论 |
| POST | `/posts/<id>/like` | 点赞/取消点赞 |

#### 📁 文件模块 `/api/files`

| 方法 | 路径 | 描述 |
|:---:|:-----|:-----|
| POST | `/` | 上传文件 |
| GET | `/<id>` | 下载文件 |

<div align="center">

📖 **详细 API 文档请访问**: [`/api/docs`](http://localhost:5000/api/docs) (Swagger UI)

</div>

---

## 🛠️ 开发指南

### ⚙️ 环境变量配置

#### 🔧 后端 `backend/.env.development`

```env
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qyquant
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
CORS_ORIGINS=http://localhost:5173
REDIS_URL=redis://localhost:6379/0
```

#### 🎨 前端 `frontend/.env.development`

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

### 🗄️ 数据库迁移

```bash
cd backend

# 创建迁移
flask db migrate -m "描述信息"

# 执行迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 🧪 运行测试

#### 🔧 后端测试

```bash
cd backend
pytest                          # 运行所有测试
pytest tests/test_backtests.py  # 运行特定测试
pytest -v                       # 详细输出
pytest --cov=app                # 生成覆盖率报告
```

#### 🎨 前端测试

```bash
cd frontend
npm test               # 运行所有测试
npm run test:ui        # Vitest UI 模式
```

### ⚙️ Celery 任务队列

```bash
cd backend

# 启动 Celery Worker
celery -A app.celery_app worker --loglevel=info

# 启动 Celery Beat (定时任务)
celery -A app.celery_app beat --loglevel=info
```

### 💻 可用命令

#### 🔧 后端 Make 命令

```bash
cd backend
make dev    # 启动开发服务器
```

#### 🎨 前端 npm 脚本

```bash
cd frontend
npm run dev       # 开发服务器
npm run build     # 生产构建
npm run preview   # 预览构建结果
npm run test      # 运行测试
```

---

## 🐛 故障排除

### ❓ PowerShell 无法激活虚拟环境

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 🔌 端口被占用

**修改后端端口**:

```python
# backend/app/config.py
DEBUG = True
PORT = 5001  # 修改端口
```

**修改前端代理**:

```typescript
// frontend/vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5001', // 修改目标端口
    }
  }
}
```

### 🗄️ 数据库连接失败

<div align="center">

1️⃣ 检查 Docker 容器状态: `docker ps`

2️⃣ 检查数据库配置: `backend/.env.development`

3️⃣ 确认 PostgreSQL 服务运行正常

</div>

### 🌐 CORS 错误

检查 `backend/app/config.py` 中的 `CORS_ORIGINS` 配置是否包含前端地址。

---

## 🗺️ 开发路线图

### ✅ MVP 阶段

<div align="center">

- [x] 🔨 前后端基础架构
- [x] 🔐 用户认证系统
- [x] 📊 策略管理模块
- [x] 📈 回测引擎框架
- [x] 🤖 机器人模拟交易
- [x] 💬 社区论坛功能
- [x] 📁 文件上传下载

</div>

### 🚧 下一阶段

<div align="center">

- [ ] 📊 实时数据源接入 (Binance/OKX)
- [ ] 🛡️ 策略沙箱执行环境
- [ ] 🔌 WebSocket 实时推送
- [ ] 📈 高级图表组件
- [ ] 🏪 策略市场功能
- [ ] 💰 实盘交易对接

</div>

### 🔮 长期规划

<div align="center">

- [ ] 📱 移动端 App (React Native)
- [ ] 🤖 策略 AI 辅助生成
- [ ] 🏦 多交易所支持
- [ ] ☁️ 云端部署方案

</div>

---

## 📄 许可证

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

</div>

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

<div align="center">

1️⃣ Fork 本仓库

2️⃣ 创建特性分支 (`git checkout -b feature/AmazingFeature`)

3️⃣ 提交更改 (`git commit -m 'Add some AmazingFeature'`)

4️⃣ 推送到分支 (`git push origin feature/AmazingFeature`)

5️⃣ 开启 Pull Request

</div>

---

## 📞 联系方式

<div align="center">

- 🐛 **报告问题**: [GitHub Issues](https://github.com/MapleQiAN/QYQuant/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/MapleQiAN/QYQuant/discussions)
- 📧 **邮件联系**: support@qyquant.com

</div>

---

## English

### 📖 Overview

QYQuant is a full-stack quantitative trading platform providing strategy backtesting, paper trading, and community features. Built with a modern frontend-backend architecture supporting both Chinese and English.

### ✨ Features

| Feature | Description |
|:---:|:---|
| 🎯 **Strategy Management** | Create, edit, and version control trading strategies |
| 📈 **Historical Backtesting** | High-performance backtesting engine powered by Celery |
| 🤖 **Paper Trading** | Simulated trading bots with real-time monitoring |
| 💬 **Community Forum** | Share strategies, comments, likes, and tipping |
| 📁 **File Management** | Upload/download strategy files with version control |
| 🔐 **User System** | JWT authentication, profiles, and social features |

### 🚀 Quick Start

#### 📋 Prerequisites

<div align="center">

![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Optional-2496ED?logo=docker&logoColor=white)

</div>

#### 🔧 Backend Setup

```bash
cd backend
docker-compose up -d
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
flask --app app run
```

<div align="center">

**🌐 Backend URL**: `http://127.0.0.1:5000`

**🔑 Default Account**: `admin / admin123`

</div>

#### 🎨 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

<div align="center">

**🌐 Frontend URL**: `http://127.0.0.1:5173`

</div>

### 📡 API Documentation

**Base URL**: `/api`

#### ✅ Success Response

```json
{ "code": 0, "message": "ok", "data": {...}, "request_id": "..." }
```

#### 🔌 Main Endpoints

<div align="center">

| Method | Endpoint | Description |
|:---:|:-----|:-----|
| POST | `/api/auth/login` | User login |
| GET | `/api/users/me` | Current user info |
| GET | `/api/strategies/recent` | Recent strategies |
| POST | `/api/backtests/run` | Create backtest job |
| GET | `/api/backtests/job/<id>` | Job status and result |
| GET | `/api/bots/recent` | Recent bots |
| GET | `/api/forum/hot` | Hot forum posts |

</div>

<div align="center">

📖 **Visit** [`/api/docs`](http://localhost:5000/api/docs) **for full Swagger documentation**

</div>

---

<div align="center">

Made with ❤️ by QYQuant Team

![GitHub stars](https://img.shields.io/github/stars/MapleQiAN/QYQuant?style=social)
![GitHub forks](https://img.shields.io/github/forks/MapleQiAN/QYQuant?style=social)

</div>
