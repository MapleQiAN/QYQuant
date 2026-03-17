# Story 2.2: 登录与 Token 刷新

Status: ready-for-dev

## Story

作为已注册用户，
我希望通过手机号验证码登录，Access Token 过期后能无感刷新，
以便在安全的前提下保持登录状态不中断。

## Acceptance Criteria (验收标准)

1. **已注册用户登录**：已注册用户提交手机号+验证码，调用 `POST /api/v1/auth/login`，验证码匹配后返回新 Access Token，并刷新 HttpOnly Cookie 中的 Refresh Token
2. **Token 刷新**：Access Token 过期但 Refresh Token 有效时，前端调用 `POST /api/v1/auth/refresh`，服务端验证 Cookie 中的 Refresh Token（未在 Redis 黑名单中），返回新 Access Token
3. **登出**：用户点击登出，调用 `POST /api/v1/auth/logout`，服务端将当前 Refresh Token 写入 Redis 黑名单，清除 Cookie；此后用该 Token 调用 /refresh 返回 401
4. **多设备管理**：每次登录生成独立的 Refresh Token，登出仅吊销当前设备的 Token

## Tasks / Subtasks

- [ ] Task 1: 实现 Token 刷新端点 (AC: #2)
  - [ ] 1.1 实现 `POST /api/v1/auth/refresh`：从 Cookie 读取 Refresh Token → SHA-256 哈希后查 `refresh_tokens` 表 → 验证未吊销+未过期 → 检查 Redis 黑名单 → 生成新 Access Token
  - [ ] 1.2 Token 轮换：每次 refresh 时生成新 Refresh Token，吊销旧的（防止 Token 窃取重放）
  - [ ] 1.3 设置新的 HttpOnly Cookie
- [ ] Task 2: 实现登出端点 (AC: #3)
  - [ ] 2.1 实现 `POST /api/v1/auth/logout`：读取 Cookie 中的 Refresh Token → 在 `refresh_tokens` 表设置 `revoked_at` → 将 Token JTI 写入 Redis 黑名单（TTL = Token 剩余有效期）→ 清除 Cookie
  - [ ] 2.2 确保已吊销 Token 调用 /refresh 返回 401
- [ ] Task 3: JWT 回调配置 (AC: #1, #2)
  - [ ] 3.1 在 Flask-JWT-Extended 配置 `@jwt.token_in_blocklist_loader` 回调，检查 Redis 黑名单
  - [ ] 3.2 配置 `@jwt.expired_token_loader` 返回统一格式的 401 响应
  - [ ] 3.3 配置 `@jwt.unauthorized_loader` 和 `@jwt.invalid_token_loader`
- [ ] Task 4: 登录端点增强 — 已注册用户路径优化 (AC: #1, #4)
  - [ ] 4.1 登录时吊销同用户的过期 Refresh Token（清理旧记录，保留其他设备活跃 Token）
  - [ ] 4.2 确保每次登录生成独立 Refresh Token（支持多设备并行登录）
- [ ] Task 5: 单元测试与集成测试 (AC: #1-#4)
  - [ ] 5.1 refresh 端点测试：有效 Token 刷新成功、过期 Token 返回 401、已吊销 Token 返回 401
  - [ ] 5.2 logout 端点测试：登出成功清除 Cookie、登出后 refresh 失败
  - [ ] 5.3 多设备测试：设备 A 登出不影响设备 B 的 Token
  - [ ] 5.4 Token 轮换测试：refresh 后旧 Token 不可再用

## Dev Notes

### 依赖 Story 2.1 的已完成工作

本 Story 假设以下已由 Story 2.1 完成：
- `User` 模型已重构（phone 字段、role、plan_level）
- `RefreshToken` 模型已创建
- `POST /api/v1/auth/send-code` 和 `POST /api/v1/auth/login` 已实现
- Redis 连接工具 `backend/app/utils/redis_client.py` 已创建
- Auth Blueprint URL 已迁移到 `/api/v1/auth`

### API 端点规范

**POST /api/v1/auth/refresh**
```json
Request:  {} （Refresh Token 从 Cookie 自动读取）
Success:  { "data": { "access_token": "new.jwt.token" } }
Headers:  Set-Cookie: refresh_token=<new_token>; HttpOnly; SameSite=Strict; Path=/api/v1/auth; Max-Age=2592000
Error 401: { "error": { "code": "TOKEN_EXPIRED", "message": "登录已过期，请重新登录" } }
Error 401: { "error": { "code": "TOKEN_REVOKED", "message": "登录已失效，请重新登录" } }
```

**POST /api/v1/auth/logout**
```json
Request:  {} （需要有效的 Access Token 或 Refresh Token）
Success:  { "data": { "message": "已成功登出" } }
Headers:  Set-Cookie: refresh_token=; HttpOnly; SameSite=Strict; Path=/api/v1/auth; Max-Age=0
Error 401: { "error": { "code": "UNAUTHORIZED", "message": "未登录" } }
```

### Token 生命周期管理

**Redis 黑名单 Key 设计：**
```
token:blacklist:{jti}  → "1"   TTL=Token剩余有效期
```

**Refresh Token 轮换策略：**
1. 客户端发送 refresh 请求（Cookie 携带旧 Token）
2. 服务端验证旧 Token 有效 → 吊销旧 Token（设置 revoked_at）
3. 生成新 Refresh Token → 存入 refresh_tokens 表 → 设置新 Cookie
4. 返回新 Access Token
5. 如果旧 Token 已被吊销（重放攻击），则吊销该用户所有 Token（安全措施）

### Flask-JWT-Extended 配置要点

```python
# backend/app/config.py 中需要添加/确认的配置
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
JWT_TOKEN_LOCATION = ["headers"]  # Access Token 仅从 Header 读取
JWT_COOKIE_SECURE = True  # 生产环境 HTTPS
JWT_COOKIE_SAMESITE = "Strict"
```

**注意：** Flask-JWT-Extended 内置的 Cookie Token 机制（`JWT_TOKEN_LOCATION = ["cookies"]`）是用于 Access Token 的，但我们的架构要求 Refresh Token 存 Cookie、Access Token 存 Header。因此 **Refresh Token 的 Cookie 管理需要手动实现**，不依赖 Flask-JWT-Extended 的 Cookie 功能。

### 关键安全逻辑

- **Token 重放检测**：如果一个已吊销的 Refresh Token 被使用（可能被窃取），立即吊销该用户的所有 Refresh Token，强制全设备重新登录
- **Redis 黑名单 TTL**：设置为 Token 剩余有效期，过期后自动清理（Token 本身也已过期）
- **Cookie 属性**：HttpOnly（防 XSS）+ SameSite=Strict（防 CSRF）+ Secure（HTTPS only，开发环境可关闭）+ Path=/api/v1/auth（最小范围）

### Project Structure Notes

**修改的文件：**
```
backend/app/
├── blueprints/
│   └── auth.py             # 新增 /refresh 和 /logout 端点
├── config.py               # 确认 JWT 配置项
└── __init__.py             # 添加 JWT 回调配置（blocklist_loader 等）
```

**新增文件：** 无（复用 Story 2.1 的 redis_client.py）

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — JWT 双令牌机制、Token 黑名单策略]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2 Story 2.2 验收标准]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR12 安全存储, NFR13 限流]
- [Source: backend/app/extensions.py — jwt = JWTManager() 已初始化]
- [Source: backend/app/blueprints/auth.py — 将在 Story 2.1 重构的 auth 蓝图基础上扩展]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
