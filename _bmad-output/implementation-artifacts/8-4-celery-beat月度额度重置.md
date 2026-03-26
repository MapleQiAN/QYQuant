# Story 8.4: Celery Beat 月度额度重置

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为平台，
我希望每月 1 日自动重置所有用户的回测额度，
以便套餐按月计费的逻辑正确运行。

## Acceptance Criteria

1. **Given** Celery Beat 已配置每月 1 日触发重置任务
   **When** 定时任务 `reset_monthly_quotas` 执行
   **Then** 将所有 `user_quota.used_count` 重置为 0
   **And** 更新每条 `user_quota.reset_at` 为下月 1 日 00:00 北京时间
   **And** 重置操作写入日志（INFO 级别），记录受影响的用户数和降级数

2. **Given** 存在已过期订阅的用户（`subscriptions.ends_at < now()` 且 `status='active'`）
   **When** 月度重置任务执行
   **Then** 将该用户的过期订阅 `status` 更新为 `expired`
   **And** 检查用户是否仍有其他未过期的 active 订阅
   **And** 若无其他 active 订阅，将 `users.plan_level` 和 `user_quota.plan_level` 降级为 `free`
   **And** 发送站内通知"您的 {原套餐等级} 套餐已过期，已恢复为免费套餐"
   **And** 降级操作写入 `audit_logs`（`action="subscription_expired"`）

3. **Given** 重置任务已执行过一次
   **When** 任务在同一天内重复执行（幂等场景）
   **Then** `used_count` 仍为 0（幂等，不产生副作用）
   **And** 已过期的订阅不重复处理（已是 `expired` 状态则跳过）
   **And** 不重复发送降级通知和审计日志

## Tasks / Subtasks

> **重要提示**：本 Story 的代码已在 commit `3ba5f6c`（feat: 实现额度管理与月度自动重置）中完整实现。以下 Task 标记为已完成，dev-story 阶段需验证现有实现是否完全满足 AC。

- [x] Task 1: 实现 `_reset_monthly_quotas()` 核心函数 (AC: #1, #2, #3)
  - [x] 1.1 在 `backend/app/tasks/quota_tasks.py` 中实现月度重置逻辑
  - [x] 1.2 Phase 1：查询过期订阅（`status='active'` 且 `ends_at < now()`），标记为 `expired`
  - [x] 1.3 检查 `has_active_subscription`：确保用户无其他未过期 active 订阅后才降级
  - [x] 1.4 降级用户：更新 `users.plan_level = 'free'`、`user_quota.plan_level = 'free'`
  - [x] 1.5 写入 `AuditLog`（`action='subscription_expired'`）和站内通知
  - [x] 1.6 Phase 2：重置所有 `UserQuota.used_count = 0`，设置 `reset_at` 为下月 1 日
  - [x] 1.7 使用 `processed_users` 集合去重，避免同一用户多次降级

- [x] Task 2: Celery 任务包装器与 Beat 调度 (AC: #1)
  - [x] 2.1 `@celery_app.task(bind=True, name='app.tasks.quota_tasks.reset_monthly_quotas')` 包装
  - [x] 2.2 支持 `has_app_context()` 判断，兼容请求上下文内外执行
  - [x] 2.3 在 `celery_app.py` 中注册 Beat schedule：`crontab(day_of_month='1', hour=0, minute=0)` UTC
  - [x] 2.4 队列：`default`

- [x] Task 3: 测试覆盖 (AC: #1, #2, #3)
  - [x] 3.1 `backend/tests/test_quota_tasks.py` — 月度重置功能测试
  - [x] 3.2 过期订阅降级测试
  - [x] 3.3 幂等性测试
  - [x] 3.4 多 active 订阅场景测试

- [ ] Task 4: 验证与审查（dev-story 阶段执行）
  - [ ] 4.1 运行 `uv run pytest tests/test_quota_tasks.py -v` 确认所有测试通过
  - [ ] 4.2 验证 AC #1：`used_count` 重置为 0，`reset_at` 正确
  - [ ] 4.3 验证 AC #2：过期订阅降级、通知、审计日志完整
  - [ ] 4.4 验证 AC #3：幂等性——重复执行无副作用
  - [ ] 4.5 **审查时区问题**：当前 Beat 调度 UTC 00:00 = 北京时间 08:00（非 AC 要求的 00:00），评估是否需要调整

## Dev Notes

### 架构约束与关键模式

- **代码已实现**：`backend/app/tasks/quota_tasks.py` 和 `celery_app.py` beat_schedule 已在 commit `3ba5f6c` 中完成。测试文件 `test_quota_tasks.py` 也已存在。
- **任务模式**：遵循项目 Celery 任务模式——`_func()` 包含实际逻辑（可在测试中直接调用），`@celery_app.task(bind=True)` 包装器处理 app context（`has_app_context()` 判断 → 若无则 `create_app()`）。
- **原子性事务**：所有操作（过期标记、降级、额度重置、审计日志、通知）在同一个 `db.session` 中，最后统一 `db.session.commit()`。
- **`next_month_start_beijing()`**：来自 `backend/app/utils/time.py`，返回下月 1 日北京时间 00:00 的 UTC datetime。用于设置 `reset_at` 字段。
- **通知服务**：`create_notification()` 来自 `backend/app/services/notifications.py`，不 commit 事务，由调用方负责。
- **审计日志**：`operator_id=None` 表示系统自动操作。`action='subscription_expired'`。

### ⚠️ 关键陷阱 1：UTC vs 北京时间

`celery_app.py` 配置 `timezone='UTC'`。当前 Beat 调度为 `crontab(day_of_month='1', hour=0, minute=0)` UTC = 北京时间 1 日 08:00。AC 要求北京时间 00:00。
- **当前方案可接受**：凌晨到 08:00 间的回测仍用上月额度，MVP 阶段影响极小。
- **精确方案 A**：修改 `celery_app.conf.timezone = 'Asia/Shanghai'`（影响所有 beat 任务，需同步确认 `run-daily-simulation` 调度正确）
- **精确方案 B**：保持 UTC，使用 `crontab(day_of_month='1', hour=16, minute=0)` 但这等于北京时间 2 日 00:00，不正确。实际上 UTC 上月最后一天 16:00 = 北京 1 日 00:00，但 crontab 无法表达"上月最后一天"。

### ⚠️ 关键陷阱 2：多 active 订阅场景

用户可能有多条 `status='active'` 的订阅（连续升级/续费）。当前实现通过 `has_active_subscription` 查询（检查是否仍有 `ends_at >= now()` 的 active 订阅）确保只有在所有订阅都过期时才降级。`processed_users` 集合避免同一用户多次处理。

### ⚠️ 关键陷阱 3：过期订阅处理顺序

**必须先处理过期订阅（Phase 1），再重置额度（Phase 2）**。这样降级用户的额度也会被正确重置，且 `plan_level` 已更新为 `free`。

### ⚠️ 关键陷阱 4：与 Story 8.3 `_activate_subscription` 的交互

`_activate_subscription`（Story 8.3）创建新 Subscription 时设置 `ends_at = starts_at + timedelta(days=31)`。月度重置任务检查 `ends_at < now_utc()` 来判断过期。31 天简化处理意味着某些月份（30/28 天）订阅可能比实际月份长 1-3 天，这是可接受的。

### ⚠️ 关键陷阱 5：测试中直接调用内部函数

测试环境中应直接调用 `_reset_monthly_quotas()` 而非 Celery 任务 `reset_monthly_quotas.delay()`。直接调用内部函数更简单可靠，避免处理 Celery worker 上下文。`CELERY_TASK_ALWAYS_EAGER` 虽然可用但不必要。

### ⚠️ 关键陷阱 6：逐行更新 vs 批量更新

当前实现使用 `for quota in quotas` 逐行更新（加载所有 UserQuota 到内存），而非 `UserQuota.query.update()`。逐行更新触发 ORM 事件，且在少量用户时性能可接受。若用户量增长到万级以上，应改为 SQL 批量 UPDATE。

### Project Structure Notes

已存在的文件（代码已实现）：
- `backend/app/tasks/quota_tasks.py` — 月度额度重置核心逻辑和 Celery 任务
- `backend/app/celery_app.py` — Beat 调度配置（`reset-monthly-quotas`）
- `backend/tests/test_quota_tasks.py` — 测试覆盖
- `backend/app/quota.py` — `normalize_plan_level()` 辅助函数
- `backend/app/utils/time.py` — `BEIJING_TZ`、`next_month_start_beijing()`、`now_utc()`
- `backend/app/services/notifications.py` — `create_notification()`

**无需修改：**
- `backend/app/models.py` — `UserQuota`（含 `reset_at`）、`Subscription`、`AuditLog` 均已存在
- 前端 — 本 Story 无前端变更

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` L1170-1183 — Story 8.4 验收标准]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1042 — 额度重置 Celery Beat 需求]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1016-1044 — 领域 7 支付系统]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1144-1148 — tasks 文件结构（quota_tasks.py）]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1209 — user_quota 表结构]
- [Source: `backend/app/tasks/quota_tasks.py` — 完整实现代码（113 行）]
- [Source: `backend/app/celery_app.py` L62-73 — Beat 调度配置]
- [Source: `backend/app/quota.py` — PLAN_LIMITS（free=10, lite=200, pro=500, expert=unlimited）]
- [Source: `backend/app/models.py` L219-225 — UserQuota 模型]
- [Source: `backend/app/utils/time.py` — `next_month_start_beijing()` 时区计算]
- [Source: `_bmad-output/implementation-artifacts/8-3-支付回调处理与套餐激活.md` — 前序 Story 实现细节]
- [Source: Git commit `3ba5f6c` — "feat: 实现额度管理与月度自动重置"]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
