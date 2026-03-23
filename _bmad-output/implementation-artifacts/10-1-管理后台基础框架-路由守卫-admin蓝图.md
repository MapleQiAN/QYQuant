# Story 10.1: 管理后台基础框架（路由守卫 + Admin 蓝图）

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为管理员，
我希望有一个受保护的管理后台入口，只有 admin 角色用户才能访问，
以便安全地执行运营管理操作。

## Acceptance Criteria

1. **前端路由守卫**：role=admin 用户登录后访问 `/admin/*` 路由，Vue Router `beforeEach` 守卫验证 `users.role === 'admin'`，非 admin 用户跳转首页并提示"无权限"
2. **后端 Admin 装饰器**：所有 `/api/v1/admin/` 端点均有 `@require_admin` Flask 装饰器，非 admin 请求返回 403 `{"error": {"code": "FORBIDDEN", "message": "管理员权限不足"}}`
3. **Admin 蓝图注册**：admin 蓝图注册至 Flask app factory，路由前缀 `/api/v1/admin/`
4. **audit_logs 表可用**：audit_logs 表已创建且可写入（id、operator_id、action、target_type、target_id、details JSONB、created_at），遵循 NFR29
5. **Admin Dashboard 页面**：创建 `/admin` 管理后台首页（AdminDashboard.vue），显示基础系统概览（占位内容即可，后续 story 填充具体功能模块）
6. **审计日志写入工具函数**：提供 `write_audit_log(operator_id, action, target_type, target_id, details)` 工具函数，供后续 admin 操作统一调用

## Tasks / Subtasks

- [ ] Task 1: 创建 `@require_admin` 装饰器 (AC: #2)
  - [ ] 1.1 在 `backend/app/utils/` 下新建 `auth_helpers.py`（或在已有 utils 模块中添加）
  - [ ] 1.2 实现 `require_admin` 装饰器：基于 `@jwt_required()` + 检查 `current_user.role == 'admin'`，非 admin 返回 403
  - [ ] 1.3 编写单元测试验证 admin/非 admin 用户的访问控制
- [ ] Task 2: 创建 Admin 蓝图并注册 (AC: #3)
  - [ ] 2.1 新建 `backend/app/blueprints/admin.py`，创建 `admin_bp` 蓝图，url_prefix=`/api/v1/admin`
  - [ ] 2.2 添加基础健康检查端点 `GET /api/v1/admin/health`（验证蓝图和装饰器工作正常）
  - [ ] 2.3 在 `backend/app/__init__.py` 的 `create_app()` 中注册 `admin_bp`
- [ ] Task 3: 确认 audit_logs 表可用 (AC: #4)
  - [ ] 3.1 验证 `AuditLog` 模型已存在（`backend/app/models.py` 第56行），确认字段完整性
  - [ ] 3.2 创建 `write_audit_log()` 工具函数封装审计日志写入逻辑（AC: #6）
  - [ ] 3.3 编写测试验证审计日志写入
- [ ] Task 4: 前端路由守卫 (AC: #1)
  - [ ] 4.1 修改 `frontend/src/router/index.ts`，添加 `/admin` 路由组，设置 `meta: { requiresAdmin: true }`
  - [ ] 4.2 在 `router.beforeEach` 中添加 admin 角色检查逻辑
  - [ ] 4.3 非 admin 用户访问时跳转首页并显示"无权限"提示（使用已有的 toast/notification 组件）
- [ ] Task 5: AdminDashboard 页面 (AC: #5)
  - [ ] 5.1 创建 `frontend/src/views/admin/AdminDashboard.vue`，包含基础管理后台布局
  - [ ] 5.2 创建 `frontend/src/api/admin.ts` API 客户端模块
  - [ ] 5.3 创建 `frontend/src/stores/useAdminStore.ts` Pinia store（如需要）
- [ ] Task 6: 端到端测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 测试 admin 用户可以正常访问 admin 端点
  - [ ] 6.2 测试普通用户访问 admin 端点返回 403
  - [ ] 6.3 测试前端路由守卫正确拦截非 admin 用户

## Dev Notes

### 架构约束与关键设计决策

**后端 - Flask 蓝图模式：**
- 所有蓝图遵循 `url_prefix='/api/v1/'` 模式，admin 蓝图使用 `/api/v1/admin/`
- 蓝图文件位置：`backend/app/blueprints/admin.py` [Source: architecture.md#领域8]
- 蓝图注册在 `backend/app/__init__.py` 的 `create_app()` 函数中 [Source: backend/app/__init__.py]

**后端 - 认证与权限模式：**
- 使用 Flask-JWT-Extended，现有装饰器为 `@jwt_required()`
- User 模型已有 `role` 字段：`db.Column(db.String(32), nullable=False, default='user')` [Source: backend/app/models.py:35]
- AuditLog 模型已存在，字段包括：id, operator_id, action, target_type, target_id, details(JSONB), created_at [Source: backend/app/models.py:56-65]
- `@require_admin` 装饰器需要新建，架构要求所有 admin 端点使用此装饰器 [Source: architecture.md#领域8]

**后端 - 响应格式：**
- 统一使用 `ok()` 和 `error_response()` 封装响应 [Source: backend/app/blueprints/*.py]
- 错误格式：`{"error": {"code": "...", "message": "..."}}`
- API 响应遵循 `{"data": ...}` wrapper 格式

**后端 - 数据库：**
- 使用 SQLAlchemy ORM + Flask-Migrate (Alembic)
- 所有时间列使用 `TIMESTAMP WITH TIME ZONE`
- audit_logs 表已在迁移 `3b1d8f6c2a4e_phone_auth.py` 中创建

**前端 - Vue Router 模式：**
- 当前路由定义在 `frontend/src/router/index.ts`（39行）
- 使用 `createWebHistory()` 模式
- 当前无任何路由守卫或角色检查
- 架构要求：`/admin/*` 路由组，`router.beforeEach` 检查 `user.role === 'admin'` [Source: architecture.md#领域8]

**前端 - 状态管理：**
- 使用 Pinia store 管理状态
- 23 个已有 store 在 `frontend/src/stores/`
- API 客户端模块在 `frontend/src/api/`（20个已有模块）
- 用户信息需从 auth store 获取 role 字段

**前端 - 页面组织：**
- 管理页面放在 `frontend/src/views/admin/` 子目录 [Source: architecture.md#完整平台项目结构]
- 架构规划的管理页面：AdminDashboard.vue、StrategyReview.vue、UserManagement.vue、BacktestMonitor.vue

### 现有代码中的关键参考

| 文件 | 作用 | 行号 |
|------|------|------|
| `backend/app/models.py` | User 模型（role 字段）| L27-54 |
| `backend/app/models.py` | AuditLog 模型 | L56-65 |
| `backend/app/__init__.py` | Flask app factory & 蓝图注册 | L53-67 |
| `backend/app/blueprints/auth.py` | 认证蓝图参考（@jwt_required 用法）| 全文 |
| `frontend/src/router/index.ts` | 路由配置 | 全文 |
| `backend/app/blueprints/marketplace.py` | audit_log 写入示例 | 全文 |
| `backend/tests/test_marketplace.py` | 审计日志测试示例 | L563+ |

### 重要：已有审计日志写入模式

现有代码中审计日志写入示例（marketplace.py 发布策略时）：
```python
from app.models import AuditLog, db
log = AuditLog(operator_id=user_id, action="strategy_publish",
               target_type="strategy", target_id=strategy_id,
               details={"review_status": "pending"})
db.session.add(log)
db.session.commit()
```

### 强制执行规则

- 数据库时间列使用 `TIMESTAMP WITH TIME ZONE`
- Python 时间操作通过 `app.utils.time` 模块
- API 响应遵循统一的 `data` / `error` wrapper 格式
- 新增路由遵循 `/api/v1/` 前缀和蓝图结构
- 命名遵循各层 `snake_case` / `camelCase` / `PascalCase` 规则
- ❌ 禁止路由内直接返回裸 dict
- ❌ 禁止 Vue 组件直接调用 fetch()，绕过 Pinia store

### Project Structure Notes

- admin 蓝图路径：`backend/app/blueprints/admin.py` → 符合已有蓝图组织模式
- 前端管理页面路径：`frontend/src/views/admin/` → 架构规划的子目录
- 无结构冲突，完全遵循统一项目结构

### Git Intelligence

最近提交模式：
- `docs: 更新项目文档与配置` - 文档更新
- `feat: 优化社区帖子互动功能` - Epic 6 社区功能
- `feat: 完善模拟托管机器人功能` - Epic 7 模拟托管
- `feat: 实现支付回调处理与套餐激活功能` - Epic 8 支付
- `feat(epic9): 实现站内通知与邮件异步发送` - Epic 9 通知

代码模式观察：
- 提交信息使用中文
- 遵循 `feat:` / `docs:` 前缀约定
- 每个 epic 独立实现，功能模块化

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#领域8] - 管理后台架构设计
- [Source: _bmad-output/planning-artifacts/architecture.md#完整平台项目结构] - 项目结构定义
- [Source: _bmad-output/planning-artifacts/epics.md#Story10.1] - Story 需求定义
- [Source: backend/app/models.py#L27-65] - User 和 AuditLog 模型
- [Source: backend/app/__init__.py#L53-67] - 蓝图注册模式
- [Source: backend/app/blueprints/auth.py] - 认证装饰器用法参考
- [Source: frontend/src/router/index.ts] - 前端路由配置

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
