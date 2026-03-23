# Story 7.2: Celery Beat 定时执行模拟策略

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为平台，
我希望每个交易日收盘后自动运行所有 active 状态的模拟机器人，
以便用户无需手动操作即可持续跟踪策略的模拟表现。

## Acceptance Criteria

1. **Given** `simulation_records` 表（bot_id、trade_date、equity、cash、daily_return、created_at）和 `simulation_positions` 表（bot_id、symbol、quantity、avg_cost、updated_at）已通过 migration 创建
   **When** Celery Beat 已配置每个交易日 16:00（北京时间）触发定时任务并执行
   **Then** 查询所有 `status=active` 的 `simulation_bots`，逐一通过 E2B 沙箱执行策略逻辑（FR42）

2. **Given** Celery Beat 触发 `run_daily_simulation` 任务
   **When** 任务执行
   **Then** 执行结果写入 `simulation_records`（trade_date、equity、cash、daily_return）
   **And** 更新 `simulation_positions`（symbol、quantity、avg_cost）

3. **Given** 某个机器人执行失败（策略报错/沙箱超时）
   **When** 该机器人任务抛出异常
   **Then** 异常被捕获并记录错误日志，**不影响**其他机器人继续运行（容错隔离）

4. **Given** Celery Beat 调度已配置
   **When** 查看 `celery_app.py` 的 `beat_schedule`
   **Then** 包含 `run-daily-simulation` 任务，cron 表达式为每天 08:00 UTC（=北京时间 16:00）

## Tasks / Subtasks

- [ ] Task 1: 数据库迁移 — 创建 `simulation_records` 表 (AC: #1)
  - [ ] 1.1 生成新 Alembic 迁移文件：
    ```bash
    flask db migrate -m "create_simulation_records_table"
    ```
  - [ ] 1.2 在 `upgrade()` 中：
    ```python
    op.create_table(
        'simulation_records',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('bot_id', sa.String(), sa.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('equity', sa.Numeric(18, 2), nullable=False),
        sa.Column('cash', sa.Numeric(18, 2), nullable=False),
        sa.Column('daily_return', sa.Numeric(10, 6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index('idx_simulation_records_bot_id', 'simulation_records', ['bot_id'])
    op.create_index('idx_simulation_records_trade_date', 'simulation_records', ['bot_id', 'trade_date'])
    ```
  - [ ] 1.3 在 `downgrade()` 中：
    ```python
    op.drop_index('idx_simulation_records_trade_date', table_name='simulation_records')
    op.drop_index('idx_simulation_records_bot_id', table_name='simulation_records')
    op.drop_table('simulation_records')
    ```
  - [ ] 1.4 运行迁移：`flask db upgrade`

- [ ] Task 2: 数据库迁移 — 创建 `simulation_positions` 表 (AC: #1)
  - [ ] 2.1 **在独立迁移文件中**生成：
    ```bash
    flask db migrate -m "create_simulation_positions_table"
    ```
  - [ ] 2.2 在 `upgrade()` 中：
    ```python
    op.create_table(
        'simulation_positions',
        sa.Column('bot_id', sa.String(), sa.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('avg_cost', sa.Numeric(18, 4), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('bot_id', 'symbol'),
    )
    ```
  - [ ] 2.3 在 `downgrade()` 中：
    ```python
    op.drop_table('simulation_positions')
    ```
  - [ ] 2.4 运行迁移：`flask db upgrade`

- [ ] Task 3: 后端 — 新增 `SimulationRecord` 和 `SimulationPosition` 模型 (AC: #1, #2)
  - [ ] 3.1 在 `backend/app/models.py` 末尾追加（在已有 `SimulationBot` 类之后）：
    ```python
    class SimulationRecord(db.Model):
        __tablename__ = 'simulation_records'
        id = db.Column(db.String, primary_key=True, default=gen_id)
        bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
        trade_date = db.Column(db.Date, nullable=False)
        equity = db.Column(db.Numeric(18, 2), nullable=False)
        cash = db.Column(db.Numeric(18, 2), nullable=False)
        daily_return = db.Column(db.Numeric(10, 6), nullable=False)
        created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    class SimulationPosition(db.Model):
        __tablename__ = 'simulation_positions'
        bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
        symbol = db.Column(db.String(20), nullable=False)
        quantity = db.Column(db.Numeric(18, 4), nullable=False)
        avg_cost = db.Column(db.Numeric(18, 4), nullable=False)
        updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
        __table_args__ = (db.PrimaryKeyConstraint('bot_id', 'symbol'),)
    ```
  - [ ] 3.2 确认 `SimulationBot` 模型（Story 7.1 创建）已存在于 `models.py`，添加两个新类到同一文件

- [ ] Task 4: 后端 — 创建 `simulation_tasks.py` Celery 任务 (AC: #1, #2, #3)
  - [ ] 4.1 创建 `backend/app/tasks/simulation_tasks.py`，实现单机器人执行函数：
    ```python
    import logging
    from datetime import date
    from decimal import Decimal

    from celery.exceptions import SoftTimeLimitExceeded
    from flask import has_app_context

    from ..celery_app import celery_app
    from ..extensions import db
    from ..models import SimulationBot, SimulationRecord, SimulationPosition
    from ..strategy_runtime import execute_backtest_strategy, StrategyRuntimeError
    from ..strategy_runtime.loader import load_strategy_package
    from ..utils.time import now_utc

    logger = logging.getLogger(__name__)

    def _execute_single_bot(bot: SimulationBot) -> None:
        """执行单个模拟机器人，失败时抛出异常（由调用方捕获）"""
        # 加载策略代码
        loaded = load_strategy_package(bot.strategy_id, version=None)  # 使用最新版本

        # 获取最新一条 simulation_record 作为上一日收盘状态
        last_record = (
            SimulationRecord.query
            .filter_by(bot_id=bot.id)
            .order_by(SimulationRecord.trade_date.desc())
            .first()
        )
        current_equity = last_record.equity if last_record else bot.initial_capital
        current_cash = last_record.cash if last_record else bot.initial_capital

        # 获取当前持仓
        positions = SimulationPosition.query.filter_by(bot_id=bot.id).all()
        positions_data = {
            p.symbol: {'quantity': float(p.quantity), 'avg_cost': float(p.avg_cost)}
            for p in positions
        }

        # 构造市场数据（用策略绑定的标的，当天最新行情）
        # 注意：模拟托管策略需要策略本身定义 symbol；此处传入 positions 和 equity 作为上下文
        outcome = execute_backtest_strategy(
            symbol=loaded.get('manifest', {}).get('symbol', '000001.XSHG'),
            bars=[],  # 模拟模式：策略自行从 market_data 获取，bars 为空列表
            loaded_strategy=loaded,
            params={
                'mode': 'simulation',
                'current_equity': float(current_equity),
                'current_cash': float(current_cash),
                'positions': positions_data,
                'trade_date': str(date.today()),
            },
            timeout_seconds=120,
        )

        # 解析执行结果
        trades = outcome.get('trades') or []
        new_equity = Decimal(str(outcome.get('equity', current_equity)))
        new_cash = Decimal(str(outcome.get('cash', current_cash)))
        prev_equity = Decimal(str(current_equity))
        daily_return = (new_equity - prev_equity) / prev_equity if prev_equity else Decimal('0')

        today = date.today()

        # 写入 simulation_records（upsert by bot_id + trade_date）
        existing = SimulationRecord.query.filter_by(bot_id=bot.id, trade_date=today).first()
        if existing:
            existing.equity = new_equity
            existing.cash = new_cash
            existing.daily_return = daily_return
        else:
            record = SimulationRecord(
                bot_id=bot.id,
                trade_date=today,
                equity=new_equity,
                cash=new_cash,
                daily_return=daily_return,
            )
            db.session.add(record)

        # 更新 simulation_positions（按 trades 中的买卖信号更新）
        new_positions = outcome.get('positions') or {}
        for symbol, pos_data in new_positions.items():
            existing_pos = SimulationPosition.query.filter_by(bot_id=bot.id, symbol=symbol).first()
            if existing_pos:
                existing_pos.quantity = Decimal(str(pos_data.get('quantity', 0)))
                existing_pos.avg_cost = Decimal(str(pos_data.get('avg_cost', 0)))
                existing_pos.updated_at = now_utc()
            else:
                new_pos = SimulationPosition(
                    bot_id=bot.id,
                    symbol=symbol,
                    quantity=Decimal(str(pos_data.get('quantity', 0))),
                    avg_cost=Decimal(str(pos_data.get('avg_cost', 0))),
                )
                db.session.add(new_pos)

        db.session.commit()
        logger.info(f"[simulation] bot={bot.id} trade_date={today} equity={new_equity} daily_return={daily_return}")
    ```
  - [ ] 4.2 实现主调度任务 `run_daily_simulation`：
    ```python
    def _run_daily_simulation():
        active_bots = SimulationBot.query.filter_by(status='active').all()
        logger.info(f"[simulation] Starting daily run for {len(active_bots)} active bots")

        for bot in active_bots:
            try:
                _execute_single_bot(bot)
            except SoftTimeLimitExceeded:
                logger.error(f"[simulation] bot={bot.id} timed out (SoftTimeLimitExceeded)")
            except StrategyRuntimeError as exc:
                logger.error(f"[simulation] bot={bot.id} strategy error: {exc.message} {exc.details}")
            except Exception as exc:
                logger.exception(f"[simulation] bot={bot.id} unexpected error: {exc}")
            # 单个机器人失败不 break，继续下一个（容错隔离）


    @celery_app.task(bind=True, name='app.tasks.simulation_tasks.run_daily_simulation')
    def run_daily_simulation(self):
        if has_app_context():
            return _run_daily_simulation()

        from .. import create_app
        app = create_app()
        with app.app_context():
            return _run_daily_simulation()
    ```

- [ ] Task 5: 后端 — 配置 Celery Beat 定时计划 (AC: #4)
  - [ ] 5.1 在 `backend/app/celery_app.py` 末尾追加 beat_schedule：
    ```python
    from celery.schedules import crontab

    celery_app.conf.beat_schedule = {
        'run-daily-simulation': {
            'task': 'app.tasks.simulation_tasks.run_daily_simulation',
            'schedule': crontab(hour=8, minute=0),  # 08:00 UTC = 16:00 北京时间
            'options': {'queue': 'simulation'},
        },
    }
    celery_app.conf.timezone = 'UTC'
    ```
  - [ ] 5.2 在 `celery_app.py` 的 `task_routes` 中追加模拟任务路由：
    ```python
    task_routes={
        'app.tasks.backtests.*': {'queue': 'backtest'},
        'app.tasks.simulation_tasks.*': {'queue': 'simulation'},
    },
    ```
  - [ ] 5.3 **重要**：只有 `status=active` 的机器人参与执行，`paused` 和 `stopped` 的跳过（查询 WHERE status='active'）

- [ ] Task 6: 后端 — 测试 (AC: #1-#4)
  - [ ] 6.1 创建 `backend/tests/test_simulation_tasks.py`：
    - `test_run_daily_simulation_creates_record`：触发任务后，active bot 对应的 `simulation_records` 创建一条记录
    - `test_run_daily_simulation_skips_paused`：`status=paused` 的机器人不会被执行（无新记录）
    - `test_run_daily_simulation_isolated_failure`：一个机器人执行抛异常，其他机器人仍然执行成功
    - `test_run_daily_simulation_updates_positions`：策略返回 positions 数据后，simulation_positions 被正确 upsert
    - `test_run_daily_simulation_upsert_same_date`：同一天重复执行，simulation_records 更新而非重复插入
  - [ ] 6.2 测试 fixture 参考（复用 Story 7.1 的 `sim_bot` fixture）：
    ```python
    @pytest.fixture
    def active_bot(db_session, auth_user, test_strategy):
        bot = SimulationBot(
            user_id=auth_user.id,
            strategy_id=test_strategy.id,
            initial_capital=100000,
            status='active',
        )
        db_session.add(bot)
        db_session.commit()
        return bot
    ```
  - [ ] 6.3 Mock `execute_backtest_strategy` 返回模拟结果，不依赖真实 E2B：
    ```python
    from unittest.mock import patch

    MOCK_OUTCOME = {
        'trades': [],
        'equity': 102000.0,
        'cash': 50000.0,
        'positions': {'000001.XSHG': {'quantity': 1000, 'avg_cost': 52.0}},
    }

    with patch('app.tasks.simulation_tasks.execute_backtest_strategy', return_value=MOCK_OUTCOME):
        run_daily_simulation()
    ```

## Dev Notes

### 架构约束与模式

- **Celery 配置文件**: `backend/app/celery_app.py`
  - Broker/Backend：Redis DB 1（`REDIS_URL` 或 `CELERY_BROKER_URL` 环境变量）
  - 并发数：`CELERYD_CONCURRENCY=10`（可配置）
  - 已有队列：`backtest`；本 Story 新增队列：`simulation`

- **任务文件路径**: `backend/app/tasks/simulation_tasks.py`（对标 `backtests.py` 的位置）

- **任务注册名称规则**: `app.tasks.simulation_tasks.run_daily_simulation`（与 `app.tasks.backtests.run_backtest_task` 格式一致）

- **Celery Beat 时区**：
  - 16:00 北京时间 = 08:00 UTC
  - `crontab(hour=8, minute=0)` + `timezone='UTC'`
  - 注意：非交易日（周末/节假日）也会触发，任务内部若需跳过非交易日需额外判断（MVP 阶段接受周末空运行）

- **E2B 沙箱调用**：参考 `backend/app/services/sandbox.py` 中的 `SandboxService.execute_strategy()` 和 `backend/app/strategy_runtime/executor.py` 中的 `execute_backtest_strategy()`

- **策略加载**：`load_strategy_package(strategy_id, version=None)` → 返回 `{'source': ..., 'entrypoint_callable': ..., 'strategy_id': ..., 'version': ...}`

- **模型访问**：通过 `db.session.get()` / `Model.query.filter_by()` 访问数据库（与 `backtests.py` 一致）

- **应用上下文**：Celery Worker 中需手动创建 Flask app context（`create_app() + app.app_context()`），参考 `backtests.py` 第 115-119 行的模式

### ⚠️ 关键陷阱：Story 7.1 前置依赖

本 Story 依赖 Story 7.1 完成以下内容：
- `SimulationBot` 模型（`backend/app/models.py`）
- `simulation_bots` 数据库表
- `backend/app/blueprints/simulation.py`（本 Story 不修改该文件，仅在任务层使用 `SimulationBot` 模型）

**开发前必须确认**：
1. `SimulationBot` 类已存在于 `models.py`
2. `simulation_bots` 表已通过 `flask db upgrade` 创建
3. 若 Story 7.1 未完成，本 Story 无法独立开发

### ⚠️ 关键陷阱：simulation_positions 表的 PRIMARY KEY

`simulation_positions` 表使用复合主键 `(bot_id, symbol)`，**不是** auto-increment id。
- 在 SQLAlchemy 模型中使用 `__table_args__ = (db.PrimaryKeyConstraint('bot_id', 'symbol'),)`
- Upsert 逻辑：先 `filter_by(bot_id=bot_id, symbol=symbol).first()`，存在则 update，不存在则 insert

### ⚠️ 关键陷阱：容错隔离（最重要！）

`for bot in active_bots:` 循环内，**每个机器人的异常必须被 try/except 捕获**。
- 捕获 `SoftTimeLimitExceeded`（Celery 软超时）
- 捕获 `StrategyRuntimeError`（策略执行错误）
- 捕获所有 `Exception`（未知错误）
- **不能 raise 或 break**，只记录日志，继续下一个机器人
- 参考 Epic 7.2 验收标准："单个机器人执行失败不影响其他机器人继续运行"

### ⚠️ 关键陷阱：beat_schedule 导入时机

`celery_app.conf.beat_schedule` 的赋值应在 `celery_app.py` 末尾，且必须在 `celery_app` 对象创建后，否则会覆盖已有配置。追加 `from celery.schedules import crontab` 导入到文件顶部或就近使用。

### ⚠️ 关键陷阱：模拟执行与回测的区别

回测 = 历史数据批量运行，`bars` 参数包含全量历史 K 线
模拟托管 = 每日增量执行，策略以当前持仓 + 当日收盘价决策

在 MVP 阶段，`_execute_single_bot` 传给 E2B 的 `bars=[]`，由策略参数中的 `positions`、`equity`、`cash`、`trade_date` 提供上下文。实际的行情数据获取逻辑（聚宽 API）由策略代码自身处理（在 E2B 沙箱中运行）。

**注意**：若策略代码未实现 simulation 模式下的行情获取，E2B 执行会失败。本 Story 的容错隔离机制会捕获此类错误，不会影响其他机器人。

### ⚠️ 关键陷阱：已有 task_routes 必须保留

修改 `celery_app.py` 中的 `task_routes` 时，**不要删除已有的 `backtest` 队列路由**：
```python
task_routes={
    'app.tasks.backtests.*': {'queue': 'backtest'},   # 保留！
    'app.tasks.simulation_tasks.*': {'queue': 'simulation'},  # 新增
},
```

### Celery Beat 启动命令

开发环境验证 Beat 配置：
```bash
# 启动 Celery Beat（在 backend/ 目录下）
celery -A app.celery_app:celery_app beat --loglevel=info

# 启动 Worker 监听 simulation 队列
celery -A app.celery_app:celery_app worker -Q simulation --loglevel=info
```

### 现有工具函数速查

```python
# Celery 任务模式（参考 backtests.py）
from ..celery_app import celery_app
@celery_app.task(bind=True, name='app.tasks.simulation_tasks.run_daily_simulation')
def run_daily_simulation(self):
    from .. import create_app
    app = create_app()
    with app.app_context():
        ...

# 时间工具
from ..utils.time import now_utc
from datetime import date
today = date.today()

# 数据库模式（与 backtests.py 一致）
from ..extensions import db
bot = db.session.get(SimulationBot, bot_id)
records = SimulationRecord.query.filter_by(bot_id=bot.id).all()

# 策略执行
from ..strategy_runtime import execute_backtest_strategy, StrategyRuntimeError
from ..strategy_runtime.loader import load_strategy_package
loaded = load_strategy_package(strategy_id, version=None)
```

### 数据流示意

```
Celery Beat (08:00 UTC)
    → run_daily_simulation task
    → 查询 SimulationBot WHERE status='active'
    → for each bot:
        → load_strategy_package(bot.strategy_id)
        → 获取 last SimulationRecord（上日收益状态）
        → 获取 SimulationPosition（当前持仓）
        → execute_backtest_strategy(E2B sandbox)
        → 写入/更新 SimulationRecord（当日收益）
        → upsert SimulationPosition（更新持仓）
        → 异常 → logger.error (continue)
```

### Project Structure Notes

```
backend/app/
├── celery_app.py                       # 修改：追加 beat_schedule + simulation 队列路由
├── models.py                           # 修改：追加 SimulationRecord + SimulationPosition 模型
├── tasks/
│   ├── backtests.py                    # 不修改（参考模式）
│   └── simulation_tasks.py            # 新建：run_daily_simulation 任务
└── tests/
    └── test_simulation_tasks.py       # 新建：任务测试

backend/migrations/versions/
├── xxxx_create_simulation_records_table.py    # Task 1
└── xxxx_create_simulation_positions_table.py  # Task 2
```

### 关键依赖关系

- **硬依赖（前置必须完成）**:
  - Story 7.1「创建模拟托管机器人与免责提示」— `SimulationBot` 模型 + `simulation_bots` 表
  - Story 3.1「Celery Redis 任务队列基础设施」— Celery 配置（`celery_app.py`）、Worker 进程已就绪
  - Story 3.3「E2B 沙箱集成与策略安全执行」— `execute_backtest_strategy` 函数可用

- **后续 Story 依赖本 Story**:
  - Story 7.3「查看机器人运行状态与持仓」— 依赖 `simulation_positions` 表和 `GET /api/v1/simulation/bots/:id/positions` 端点
  - Story 7.4「查看模拟收益曲线与买卖信号（SSE）」— 依赖 `simulation_records` 表数据

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2: Celery Beat 定时执行模拟策略]
- [Source: _bmad-output/planning-artifacts/architecture.md#领域 6：模拟托管 & 实时推送（FR40-48）]
- [Source: _bmad-output/planning-artifacts/architecture.md#任务队列：Celery + Redis]
- [Source: backend/app/celery_app.py] — Celery 配置（broker、backend、task_routes、concurrency）
- [Source: backend/app/tasks/backtests.py] — Celery 任务注册模式 + app context 处理
- [Source: backend/app/services/sandbox.py] — E2B SandboxService.execute_strategy() 接口
- [Source: backend/app/strategy_runtime/executor.py] — execute_backtest_strategy() 调用方式
- [Source: _bmad-output/implementation-artifacts/7-1-创建模拟托管机器人与免责提示.md] — Story 7.1 实现，SimulationBot 模型定义
- [Source: _bmad-output/planning-artifacts/architecture.md#ARCH-12] — SSE 实时推送（Story 7.4 相关）

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
