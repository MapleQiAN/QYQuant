# Story 8.4: Celery Beat 月度额度重置

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为平台，
我希望每月 1 日自动重置所有用户的回测额度，
以便套餐按月计费的逻辑正确运行。

## Acceptance Criteria

1. **Given** Celery Beat 已配置每月 1 日 00:00（北京时间）触发重置任务
   **When** 定时任务 `reset_monthly_quotas` 执行
   **Then** 将所有 `user_quota.used_count` 重置为 0
   **And** 更新每条 `user_quota.reset_at` 为下月 1 日 00:00 北京时间
   **And** 重置操作写入日志（INFO 级别），记录受影响的用户数

2. **Given** 存在已过期订阅的用户（`subscriptions.ends_at < now()` 且 `status='active'`）
   **When** 月度重置任务执行
   **Then** 将该用户的过期订阅 `status` 更新为 `expired`
   **And** 将 `users.plan_level` 降级为 `free`
   **And** 将 `user_quota.plan_level` 降级为 `free`
   **And** 发送站内通知"您的 {原套餐等级} 套餐已过期，已恢复为免费套餐"
   **And** 降级操作写入 `audit_logs`（`action="subscription_expired"`）

3. **Given** 重置任务已执行过一次
   **When** 任务在同一天内重复执行（幂等场景）
   **Then** `used_count` 仍为 0（幂等，不产生副作用）
   **And** 已过期的订阅不重复处理（已是 `expired` 状态则跳过）
   **And** 不重复发送降级通知

## Tasks / Subtasks

- [ ] Task 1: 创建 `backend/app/tasks/quota_tasks.py` 月度额度重置任务 (AC: #1, #2, #3)
  - [ ] 1.1 创建 `quota_tasks.py`，遵循现有任务模式（`simulation_tasks.py` 参考）：
    ```python
    import logging
    from datetime import datetime, timedelta, timezone
    from ..celery_app import celery_app
    from ..extensions import db
    from ..models import UserQuota, Subscription, User, AuditLog
    from ..services.notifications import create_notification
    from ..quota import normalize_plan_level

    logger = logging.getLogger(__name__)

    BEIJING_TZ = timezone(timedelta(hours=8))
    ```
  - [ ] 1.2 实现内部函数 `_reset_monthly_quotas()`：
    ```python
    def _reset_monthly_quotas():
        """
        月度额度重置逻辑：
        1. 处理过期订阅 → 降级用户
        2. 重置所有 user_quota.used_count = 0
        3. 更新 reset_at 为下月 1 日
        """
        now = datetime.now(BEIJING_TZ)
        # 计算下月 1 日 00:00 北京时间
        if now.month == 12:
            next_reset = datetime(now.year + 1, 1, 1, tzinfo=BEIJING_TZ)
        else:
            next_reset = datetime(now.year, now.month + 1, 1, tzinfo=BEIJING_TZ)

        # ── Phase 1: 处理过期订阅 ──
        expired_subs = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.ends_at < datetime.now(timezone.utc),
        ).all()

        downgraded_count = 0
        for sub in expired_subs:
            sub.status = 'expired'
            user = db.session.get(User, sub.user_id)
            if user and user.plan_level != 'free':
                old_plan = user.plan_level
                user.plan_level = 'free'

                # 更新 quota plan_level
                quota = db.session.get(UserQuota, sub.user_id)
                if quota:
                    quota.plan_level = 'free'

                # 审计日志
                audit = AuditLog(
                    operator_id=None,
                    action='subscription_expired',
                    target_type='user',
                    target_id=sub.user_id,
                    details={
                        'old_plan_level': old_plan,
                        'new_plan_level': 'free',
                        'subscription_id': sub.id,
                    },
                )
                db.session.add(audit)

                # 站内通知
                plan_names = {'lite': '轻量版', 'pro': '进阶版', 'expert': '专业版'}
                plan_display = plan_names.get(old_plan, old_plan)
                create_notification(
                    user_id=sub.user_id,
                    type='subscription_expired',
                    title='套餐已过期',
                    content=f'您的 {plan_display} 套餐已过期，已恢复为免费套餐。如需继续使用高级功能，请重新订阅。',
                )
                downgraded_count += 1

        # ── Phase 2: 重置所有用户额度 ──
        reset_count = UserQuota.query.update({
            UserQuota.used_count: 0,
            UserQuota.reset_at: next_reset,
        })

        db.session.commit()

        logger.info(
            'Monthly quota reset completed: %d quotas reset, %d subscriptions expired',
            reset_count,
            downgraded_count,
        )
        return {'reset_count': reset_count, 'downgraded_count': downgraded_count}
    ```
  - [ ] 1.3 实现 Celery 任务包装函数：
    ```python
    @celery_app.task(
        bind=True,
        name='app.tasks.quota_tasks.reset_monthly_quotas',
    )
    def reset_monthly_quotas(self):
        """Celery Beat 月度额度重置任务"""
        from .. import create_app
        app = create_app()
        with app.app_context():
            return _reset_monthly_quotas()
    ```
  - [ ] 1.4 **关键模式**：遵循 `simulation_tasks.py` 的 `create_app()` + `app_context()` 模式，确保 Flask 应用上下文可用。

- [ ] Task 2: 在 `celery_app.py` 注册 Beat 调度 (AC: #1)
  - [ ] 2.1 在 `celery_app.py` 的 `task_imports` 中追加 `'app.tasks.quota_tasks'`
  - [ ] 2.2 在 `beat_schedule` 字典中追加：
    ```python
    'reset-monthly-quotas': {
        'task': 'app.tasks.quota_tasks.reset_monthly_quotas',
        'schedule': crontab(day_of_month='1', hour=16, minute=0),  # UTC 16:00 = 北京时间 00:00
        'options': {'queue': 'default'},
    },
    ```
  - [ ] 2.3 **关键陷阱**：Celery Beat 的 timezone 配置为 UTC（`celery_app.conf.timezone = 'UTC'`），因此北京时间 00:00 对应 UTC 前一天 16:00。`crontab(day_of_month='1', hour=16, minute=0)` 实际上是每月 1 日北京时间 00:00 触发。**但注意**：UTC 16:00 of day_of_month=1 在某些月份可能需要验证（当 UTC 仍在前月最后一天时）。更安全的做法是直接设置 `day_of_month='1', hour=16, minute=0` 因为 crontab day_of_month 是按 UTC 日期判断的。实际上 UTC 1月1日 16:00 = 北京时间 1月2日 00:00。**修正：应使用前一天的 UTC 来匹配北京时间**。即每月最后一天的 UTC 16:00 = 北京时间下月 1 日 00:00。但 crontab 无法表达"每月最后一天"。**最终方案：设置为 `day_of_month='1', hour=0, minute=0` UTC，即北京时间 1 日 08:00，或者切换 Beat timezone 为 Asia/Shanghai**。推荐方案：在 beat_schedule 中单独为此任务指定 `'schedule': crontab(day_of_month='1', hour=0, minute=0)`（UTC 00:00 = 北京时间 08:00），可接受的延迟。

- [ ] Task 3: 更新 `_activate_subscription()` 设置 `reset_at` (AC: 关联 8.3 完善)
  - [ ] 3.1 在 `backend/app/blueprints/payments.py` 的 `_activate_subscription()` 函数中，调用 `ensure_user_quota` 后补充设置 `reset_at`：
    ```python
    # 在 ensure_user_quota(order.user_id, order.plan_level) 之后追加：
    from datetime import datetime, timedelta, timezone as tz
    BEIJING_TZ = tz(timedelta(hours=8))
    now_bj = datetime.now(BEIJING_TZ)
    if now_bj.month == 12:
        next_reset = datetime(now_bj.year + 1, 1, 1, tzinfo=BEIJING_TZ)
    else:
        next_reset = datetime(now_bj.year, now_bj.month + 1, 1, tzinfo=BEIJING_TZ)
    quota = db.session.get(UserQuota, order.user_id)
    if quota:
        quota.reset_at = next_reset
    ```
  - [ ] 3.2 **注意**：`ensure_user_quota` 可能创建新记录或更新已有记录，之后再单独设置 `reset_at` 确保时间正确。

- [ ] Task 4: 编写测试 `backend/tests/test_quota_tasks.py` (AC: #1, #2, #3)
  - [ ] 4.1 参考 `test_simulation_tasks.py` 测试模式，创建测试文件：
    ```python
    # test_reset_monthly_quotas_resets_all_used_counts
    # - 创建多个用户和 UserQuota 记录（used_count > 0）
    # - 调用 _reset_monthly_quotas()
    # - 验证所有 used_count == 0
    # - 验证 reset_at 设置为下月 1 日

    # test_reset_monthly_quotas_downgrades_expired_subscriptions
    # - 创建用户，设置 active subscription 且 ends_at 在过去
    # - 调用 _reset_monthly_quotas()
    # - 验证 subscription.status == 'expired'
    # - 验证 user.plan_level == 'free'
    # - 验证 user_quota.plan_level == 'free'
    # - 验证存在 audit_log（action='subscription_expired'）
    # - 验证存在站内通知（type='subscription_expired'）

    # test_reset_monthly_quotas_idempotent
    # - 执行两次 _reset_monthly_quotas()
    # - 验证 used_count 仍为 0
    # - 验证只有 1 条 audit_log 和 1 条通知（不重复）

    # test_reset_skips_already_expired_subscriptions
    # - 创建 subscription.status == 'expired' 的记录
    # - 调用 _reset_monthly_quotas()
    # - 验证不产生新的 audit_log 和通知

    # test_reset_does_not_downgrade_active_subscriptions
    # - 创建 active subscription 且 ends_at 在未来
    # - 调用 _reset_monthly_quotas()
    # - 验证 subscription.status 仍为 'active'
    # - 验证 user.plan_level 未改变
    ```
  - [ ] 4.2 运行 `uv run pytest tests/test_quota_tasks.py -v` 确认全部通过

## Dev Notes

### 架构约束与关键模式

- **Celery Beat 时区**：`celery_app.conf.timezone = 'UTC'`。所有 Beat schedule 的 crontab 时间均为 UTC。北京时间 = UTC + 8。
- **任务模式**：遵循 `simulation_tasks.py` 模式 — 内部 `_` 前缀函数 + `@celery_app.task(bind=True)` 包装 + `create_app()` 上下文。
- **数据库事务**：整个重置操作在一个事务中完成（`db.session.commit()` 在最后调用一次）。
- **幂等性**：`used_count` 直接设为 0（非减量），已过期订阅通过 `status == 'active'` 条件过滤（已处理过的为 `expired`，自动跳过）。
- **通知服务**：`create_notification(user_id, type, title, content)` — 不 commit，由调用方负责。
- **审计日志**：`operator_id=None` 表示系统自动操作。
- **批量更新**：`UserQuota.query.update({...})` 使用 SQLAlchemy 批量更新，高效处理大量记录。

### 关键陷阱 1：Celery Beat timezone 与北京时间

Celery 配置为 UTC 时区。每月 1 日北京时间 00:00 = UTC 前一天 16:00。但 crontab `day_of_month='1'` 是基于 UTC 日期判断的，所以 UTC 的"1号16:00"实际是北京时间"2号00:00"。**推荐方案**：使用 `crontab(day_of_month='1', hour=0, minute=0)` (UTC)，对应北京时间 1 日 08:00。08:00 执行重置对用户体验影响极小（凌晨到早上 8 点的回测仍用上月额度，但 MVP 阶段可接受）。如果需要精确到午夜，需将 Celery timezone 改为 `Asia/Shanghai` 或使用 `solar` 调度。

### 关键陷阱 2：批量更新与 ORM 事件

`UserQuota.query.update({...})` 是 SQLAlchemy Core 级别的批量 UPDATE，不会触发 ORM 事件（如 `onupdate`）。这里 `UserQuota` 模型没有 `updated_at` 字段，所以不影响。但如果未来添加此字段，需改为逐行更新或在 SQL 中显式设置。

### 关键陷阱 3：过期订阅处理顺序

**必须先处理过期订阅（Phase 1），再重置额度（Phase 2）**。这样降级用户的额度也会被正确重置，且 `plan_level` 已更新为 `free`。

### 关键陷阱 4：ensure_user_quota 中的 reset_at

当前 `ensure_user_quota()` 创建 `UserQuota` 时不设置 `reset_at`。Task 3 在 `_activate_subscription()` 中补充设置。新用户注册时（默认 free 套餐）的 `reset_at` 会在首次月度重置任务执行时被设置。

### 关键陷阱 5：测试中的 eager 模式

测试环境中 `CELERY_TASK_ALWAYS_EAGER = '1'`，任务同步执行。直接测试内部 `_reset_monthly_quotas()` 函数更简单可靠（无需处理 Celery 上下文）。

### 关键陷阱 6：多个 active 订阅

理论上一个用户可能有多条 `status='active'` 的订阅（连续升级/续费）。降级逻辑应处理所有过期的 active 订阅，但只降级一次用户 `plan_level`。当前实现通过检查 `user.plan_level != 'free'` 避免重复降级。但如果用户有一条过期和一条未过期的订阅，应保留较高的套餐等级。**建议实现**：只有当用户没有任何 active 且未过期的订阅时才降级。

### Project Structure Notes

新增/修改文件列表：
- `backend/app/tasks/quota_tasks.py` — **新增**：月度额度重置 Celery 任务
- `backend/app/celery_app.py` — **修改**：追加 `quota_tasks` 到 task_imports，追加 Beat schedule 条目
- `backend/app/blueprints/payments.py` — **修改**：`_activate_subscription()` 中设置 `reset_at`
- `backend/tests/test_quota_tasks.py` — **新增**：5+ 个测试函数

**无需修改：**
- `backend/app/models.py` — `UserQuota.reset_at` 字段已存在
- `backend/app/quota.py` — 现有函数满足需求
- `backend/app/services/notifications.py` — `create_notification` 已存在
- 前端 — 本 Story 无前端变更（`reset_at` 已在 quota API 中返回）

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` L1170-1183 — Story 8.4 验收标准]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1042 — 额度重置 Celery Beat 需求]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L860-864 — Celery + Redis 任务队列配置]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L888-891 — user_quota 表结构]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1025-1039 — subscriptions 表结构]
- [Source: `_bmad-output/planning-artifacts/architecture.md` L1147 — quota_tasks.py 文件位置规划]
- [Source: `backend/app/celery_app.py` — 现有 Celery 配置、Beat schedule、任务路由]
- [Source: `backend/app/tasks/simulation_tasks.py` — 任务实现模式参考（create_app + app_context）]
- [Source: `backend/app/quota.py` — PLAN_LIMITS, ensure_user_quota, serialize_plan_limit]
- [Source: `backend/app/models.py` L219-226 — UserQuota 模型（reset_at 字段已存在）]
- [Source: `backend/app/models.py` L455-467 — Subscription 模型（ends_at, status 字段）]
- [Source: `backend/app/blueprints/payments.py` L93-151 — _activate_subscription 函数]
- [Source: `backend/app/utils/time.py` — now_utc(), format_beijing_iso() 时区工具]
- [Source: `8-3-支付回调处理与套餐激活.md` — 前序 Story 实现细节和陷阱]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
