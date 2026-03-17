# Story 3.1: Celery + Redis 任务队列基础设施

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为平台，
我希望搭建 Celery + Redis 任务队列基础设施，
以便回测任务可以异步执行并支持水平扩展。

## 验收标准

1. **Redis 实例已运行，Celery Worker 已启动**
   - Given Redis 实例已运行，Celery Worker 已启动
   - When 提交一个回测任务到队列
   - Then 任务在 5 秒内进入 pending 或 running 状态（NFR1）

2. **多 Worker 并发处理**
   - And 多个 Worker 可同时处理不同任务（最多 10 个并发，`CELERYD_CONCURRENCY=10`）

3. **backtest_jobs 表已创建**
   - And backtest_jobs 表已创建，包含字段：id、user_id、strategy_id、status ENUM('pending','running','completed','failed','timeout')、params JSONB、result_summary JSONB、result_storage_key TEXT、error_message TEXT、started_at TIMESTAMPTZ、completed_at TIMESTAMPTZ、created_at TIMESTAMPTZ

4. **user_quota 表已创建**
   - And user_quota 表已创建，包含字段：user_id、plan_level、used_count INT DEFAULT 0、reset_at TIMESTAMPTZ

5. **任务隔离**
   - And 单个任务失败不影响其他任务（NFR8）

## 任务 / 子任务

- [ ] Task 1: 升级 Celery 配置为生产级 (AC: #1, #2, #5)
  - [ ] 1.1 重构 `backend/app/celery_app.py`，添加 Redis DB 编号分离（broker 用 DB 1，auth 黑名单用 DB 0）
  - [ ] 1.2 添加 `CELERYD_CONCURRENCY=10` 可配置并发限制
  - [ ] 1.3 配置任务序列化（JSON）、结果后端（Redis）、任务超时、重试策略
  - [ ] 1.4 配置任务路由（backtest 队列隔离）
  - [ ] 1.5 添加 `task_acks_late=True` 确保任务失败后可被其他 Worker 重新拉取
  - [ ] 1.6 配置 `task_reject_on_worker_lost=True` 确保 Worker 异常退出时任务不丢失

- [ ] Task 2: 创建 backtest_jobs 数据库模型和迁移 (AC: #3)
  - [ ] 2.1 在 `backend/app/models.py` 中创建 `BacktestJob` 模型（替代或共存现有 `Backtest` 模型）
  - [ ] 2.2 status 字段使用 SQLAlchemy Enum 类型：pending, running, completed, failed, timeout
  - [ ] 2.3 params 和 result_summary 使用 JSONB 类型
  - [ ] 2.4 添加外键关联：user_id → users.id, strategy_id → strategies.id
  - [ ] 2.5 添加索引：(user_id, created_at DESC), (status), (strategy_id)
  - [ ] 2.6 创建 Alembic 数据库迁移脚本

- [ ] Task 3: 创建 user_quota 数据库模型和迁移 (AC: #4)
  - [ ] 3.1 在 `backend/app/models.py` 中创建 `UserQuota` 模型
  - [ ] 3.2 plan_level 使用 String 类型（free, basic, pro, enterprise）
  - [ ] 3.3 添加唯一约束：user_id
  - [ ] 3.4 创建 Alembic 数据库迁移脚本

- [ ] Task 4: 重构回测任务为生产级 Celery Task (AC: #1, #5)
  - [ ] 4.1 重构 `backend/app/tasks/backtests.py`，任务签名接受 `job_id` 而非原始参数
  - [ ] 4.2 任务开始时更新 backtest_jobs.status = 'running'，设置 started_at
  - [ ] 4.3 任务成功时更新 status = 'completed'，写入 result_summary，设置 completed_at
  - [ ] 4.4 任务失败时更新 status = 'failed'，写入 error_message
  - [ ] 4.5 添加 `soft_time_limit=300`（5分钟超时），超时时 status = 'timeout'
  - [ ] 4.6 使用 try/except 确保单任务失败不影响其他任务（NFR8）

- [ ] Task 5: 添加环境配置和 Docker Compose 支持 (AC: #1)
  - [ ] 5.1 在 `.env.development` 中添加 `REDIS_URL=redis://localhost:6379/1`
  - [ ] 5.2 在 `docker-compose.yml`（或创建）中添加 Redis 服务
  - [ ] 5.3 添加 Celery Worker 启动命令到项目文档或脚本
  - [ ] 5.4 添加 Flower 监控服务配置（可选，用于开发调试）

- [ ] Task 6: 编写测试 (AC: #1-#5)
  - [ ] 6.1 测试 Celery eager 模式下任务提交和执行
  - [ ] 6.2 测试 BacktestJob 模型 CRUD 操作
  - [ ] 6.3 测试 UserQuota 模型 CRUD 操作
  - [ ] 6.4 测试任务状态流转：pending → running → completed/failed/timeout
  - [ ] 6.5 测试任务失败隔离（一个任务失败不影响其他任务）

## Dev Notes

### 架构模式与约束

- **技术栈**：Python 3.11 + Flask + SQLAlchemy + Celery + Redis
- **数据库**：PostgreSQL（已有，使用 Flask-Migrate/Alembic 管理迁移）
- **Celery Broker**：Redis，与 Auth Token 黑名单**共用同一 Redis 实例**但使用**不同 DB 编号**
  - DB 0：Auth Refresh Token 黑名单（Epic 2 使用）
  - DB 1：Celery Broker
- **并发模型**：`CELERYD_CONCURRENCY=10`，可通过环境变量配置
- **Worker 扩展性**：NFR16 要求 15 分钟内可扩容至 2 倍

### 现有代码分析（关键！）

**⚠️ 已有实现需要重构，不是从零开始：**

1. **`backend/app/celery_app.py`**（第1-17行）：已有基础 Celery 配置
   - 支持 eager 模式（测试用）✓
   - **缺少**：Redis DB 编号、并发限制、序列化配置、超时设置、任务路由

2. **`backend/app/tasks/backtests.py`**（第1-27行）：已有基础任务
   - 直接传原始参数（symbol, interval 等），**需要重构为传 job_id**
   - 缺少状态管理、错误处理、超时控制

3. **`backend/app/models.py`**（第53-65行）：已有 `Backtest` 模型
   - 字段与架构规范的 `backtest_jobs` **不匹配**
   - 缺少 params JSONB, result_storage_key, error_message 等字段
   - **建议**：创建新的 `BacktestJob` 模型，保留旧 `Backtest` 模型做兼容过渡（或直接替换，取决于是否有前端依赖）

4. **`backend/app/backtest/engine.py`**（第68-107行）：回测引擎逻辑
   - 当前直接执行回测，**后续 Story 3.3 将改为 E2B 沙箱执行**
   - 本 Story 不改动引擎逻辑，只改任务调度层

### 项目结构参考

```
backend/app/
├── celery_app.py           # 需重构：生产级 Celery 配置
├── tasks/
│   ├── backtests.py        # 需重构：job_id 驱动的任务
│   ├── backtest_tasks.py   # 架构规划（可考虑重命名）
│   ├── quota_tasks.py      # 架构规划（后续 Story）
│   └── notification_tasks.py # 架构规划（后续 Story）
├── models.py               # 需新增 BacktestJob, UserQuota 模型
├── backtest/
│   ├── engine.py           # 不改动（本 Story 不涉及）
│   └── providers.py        # 不改动
└── blueprints/
    └── backtest.py         # 架构规划（后续 Story 3.4 创建 API）
```

### 测试标准

- 使用 pytest + `CELERY_TASK_ALWAYS_EAGER=true` 进行单元测试
- 模型测试使用 Flask 测试客户端 + 内存数据库（SQLite）或测试用 PostgreSQL
- 测试覆盖：任务提交、状态流转、超时处理、错误隔离

### 关键技术细节

**Celery 配置要点：**
```python
# 参考配置（非最终代码，仅供理解）
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    worker_concurrency=int(os.getenv('CELERYD_CONCURRENCY', 10)),
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,  # 5 min
    task_time_limit=330,       # hard limit
    task_routes={
        'app.tasks.backtests.*': {'queue': 'backtest'},
    },
)
```

**BacktestJob 状态机：**
```
pending → running → completed
                  → failed
                  → timeout
```

**额度扣减时机：** 本 Story 仅创建 user_quota 表结构。扣减逻辑在 Story 3.4（回测任务提交与额度管理）中实现。

### Project Structure Notes

- `BacktestJob` 模型与现有 `Backtest` 模型共存，后续迁移时可清理
- Redis DB 编号约定需在 `.env` 文件中明确记录，供 Epic 2（auth）和 Epic 3（celery）共同遵守
- 所有新增数据库表使用 TIMESTAMPTZ 类型（非 BigInteger），与架构规范对齐

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#领域2：回测引擎架构（FR10-24）] — Celery + Redis 架构、backtest_jobs/user_quota 表结构
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1] — 用户故事和验收标准
- [Source: backend/app/celery_app.py] — 现有 Celery 配置（需重构）
- [Source: backend/app/tasks/backtests.py] — 现有任务定义（需重构）
- [Source: backend/app/models.py#Backtest] — 现有 Backtest 模型（需对齐架构规范）
- [Source: backend/app/config.py] — Flask 配置（需添加 Redis/Celery 相关配置）

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `py -m py_compile backend/app/models.py backend/app/config.py backend/app/celery_app.py backend/app/tasks/backtests.py backend/app/blueprints/backtests.py backend/app/schemas.py backend/migrations/versions/4d2f6b3a9c1e_backtest_jobs_infra.py`
- `py -m pytest backend/tests/test_backtests.py backend/tests/test_models.py backend/tests/test_auth.py backend/tests/test_schemas.py backend/tests/test_backtest_summary.py -v`
- `py -m pytest backend/tests -v`

### Completion Notes List

- 用 `BacktestJob` 直接替换旧 `Backtest` 模型，并新增 `UserQuota` 模型。
- `/api/backtests/run` 与 `/api/backtests/job/<job_id>` 已切到 `backtest_jobs` 语义，任务状态以数据库为准。
- Celery 回测任务已改为 `job_id` 驱动，持久化 `pending/running/completed/failed/timeout` 状态，并保留成功任务的完整结果用于调试。
- `/api/backtests/latest` 继续保留为同步调试入口，不写入任务表。
- 新增 Redis 分库和生产级 Celery 配置，并补充本地 Docker Compose 的 worker/Flower 支持。
- 新增 Alembic 迁移：将旧 `backtests` 重命名迁移到 `backtest_jobs`，保留历史数据并创建 `user_quota`。
- 已完成完整后端回归验证。

### File List

- `backend/app/models.py`
- `backend/app/config.py`
- `backend/app/celery_app.py`
- `backend/app/tasks/backtests.py`
- `backend/app/blueprints/backtests.py`
- `backend/app/schemas.py`
- `backend/tests/conftest.py`
- `backend/tests/test_backtests.py`
- `backend/tests/test_models.py`
- `backend/tests/test_strategy_runtime.py`
- `backend/docker-compose.yml`
- `backend/Dockerfile.celery`
- `backend/.env.test`
- `backend/.env.development`
- `backend/.env.production`
- `backend/migrations/versions/4d2f6b3a9c1e_backtest_jobs_infra.py`
