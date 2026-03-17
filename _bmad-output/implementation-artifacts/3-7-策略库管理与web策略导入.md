# Story 3.7: 策略库管理与 Web 策略导入

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为已登录用户，
我希望管理我的策略库（查看、删除），并能通过拖拽上传 .qys 文件导入策略，
以便有序管理我的所有策略。

## 验收标准

1. **策略列表查询**
   - Given 用户访问"我的策略库"页
   - When 调用 `GET /api/v1/strategies/`
   - Then 返回当前用户的策略列表（名称、分类、创建时间、来源），支持分页（FR58）

2. **策略删除**
   - When 用户删除某策略
   - Then 调用 `DELETE /api/v1/strategies/:id` 成功，列表刷新

3. **.qys 文件导入**
   - Given 用户拖拽 .qys 文件到导入区域（QYSP-FR7）
   - When 文件上传完成
   - Then 后端解析 strategy.json 并展示策略元数据（名称、描述、标签）

4. **SHA256 完整性校验**
   - And SHA256 校验失败时提示"文件完整性校验失败"

5. **加密存储并跳转**
   - And 校验通过后策略 AES-256-GCM 加密存储，跳转至参数配置页

## 任务 / 子任务

- [ ] Task 1: 创建策略列表 API (AC: #1)
  - [ ] 1.1 在 `backend/app/blueprints/strategies.py` 中创建/扩展 `GET /api/v1/strategies/` 端点
  - [ ] 1.2 返回当前用户的策略列表，字段：id、name/title、category、created_at、source（'upload'/'marketplace'）
  - [ ] 1.3 支持分页：`?page=1&per_page=20`
  - [ ] 1.4 支持排序：`?sort=created_at&order=desc`
  - [ ] 1.5 只返回当前用户的策略（owner_id/author_id 过滤）

- [ ] Task 2: 创建策略删除 API (AC: #2)
  - [ ] 2.1 创建 `DELETE /api/v1/strategies/:id` 端点
  - [ ] 2.2 权限校验：只能删除自己的策略
  - [ ] 2.3 删除时同时清理：加密代码、对象存储中的 .qys 原始包
  - [ ] 2.4 检查是否有关联的 backtest_jobs，如有则软删除（标记为已删除）

- [ ] Task 3: 实现 .qys 文件上传和解析 (AC: #3, #4)
  - [ ] 3.1 创建 `POST /api/v1/strategies/import` 端点，接受 multipart/form-data
  - [ ] 3.2 .qys 文件大小限制（如 10MB）
  - [ ] 3.3 解析 .qys 文件（tar.gz 格式），提取 strategy.json
  - [ ] 3.4 验证 strategy.json 格式（使用 QYSP 包的 JSON Schema 验证器）
  - [ ] 3.5 SHA256 完整性校验（对比 strategy.json 中的 checksum 与实际文件哈希）
  - [ ] 3.6 校验失败返回 422 + `{"error": {"code": "INTEGRITY_CHECK_FAILED", "message": "文件完整性校验失败"}}`

- [ ] Task 4: 实现策略加密存储 (AC: #5)
  - [ ] 4.1 校验通过后，提取策略代码（src/strategy.py）
  - [ ] 4.2 使用 AES-256-GCM 加密（复用 Story 3.3 的 crypto.py）
  - [ ] 4.3 创建 Strategy 记录：title、description、tags、category（从 strategy.json 提取）
  - [ ] 4.4 存储字段：code_encrypted、code_hash（SHA256）
  - [ ] 4.5 .qys 原始包存对象存储，路径做 UUID 混淆（storage_key）
  - [ ] 4.6 返回新策略 ID，前端跳转到参数配置页

- [ ] Task 5: 前端策略库页面 (AC: #1, #2, #3, #4, #5)
  - [ ] 5.1 创建 `frontend/src/views/StrategyLibrary.vue`（或扩展现有策略页面）
  - [ ] 5.2 策略列表：表格或卡片展示，支持分页
  - [ ] 5.3 删除按钮：确认对话框 + 调用删除 API
  - [ ] 5.4 拖拽上传区域：支持 .qys 文件拖拽或点击上传
  - [ ] 5.5 上传后展示策略元数据预览（名称、描述、标签）
  - [ ] 5.6 校验失败时显示错误提示
  - [ ] 5.7 导入成功后跳转参数配置页

- [ ] Task 6: 编写测试 (AC: #1-#5)
  - [ ] 6.1 测试策略列表 API（分页、排序、权限过滤）
  - [ ] 6.2 测试策略删除 API（权限校验、关联数据处理）
  - [ ] 6.3 测试 .qys 文件上传和解析
  - [ ] 6.4 测试 SHA256 校验失败场景
  - [ ] 6.5 测试加密存储流程
  - [ ] 6.6 前端：上传组件交互测试

## Dev Notes

### 架构模式与约束

- **QYSP 格式**：.qys 文件是 tar.gz 格式，内含 strategy.json（元数据）+ src/strategy.py（策略代码）
- **加密**：AES-256-GCM，密钥从环境变量读取（复用 Story 3.3 的 crypto.py）
- **对象存储**：.qys 原始包存对象存储，路径做 UUID 混淆
- **分页**：使用 offset/limit 分页（MVP 简单方案）

### 现有代码分析（关键！）

1. **`backend/app/blueprints/strategies.py`**：已有策略相关端点
   - 需要检查现有端点并扩展

2. **`backend/app/models.py`** 中 `Strategy` 模型：
   - 当前字段：name、symbol、status、returns 等基础字段
   - 架构规范要求扩展：title、description、tags TEXT[]、category ENUM、code_encrypted、code_hash、storage_key、author_id
   - Story 3.3 应已添加 code_encrypted、code_hash

3. **`packages/qysp/`**：QYSP SDK
   - `qysp.validator` 模块可用于验证 strategy.json
   - `qysp.cli` 中的 `build` 命令可作为 .qys 解析的参考

4. **`backend/app/models.py`** 中 `StrategyVersion` 模型：
   - 已有版本管理（strategy_id、version、file_id、checksum）
   - 可以复用或对齐

### 项目结构参考

```
backend/app/
├── blueprints/
│   └── strategies.py       # 扩展：列表/删除/导入 API
├── services/
│   └── strategy_import.py  # 新建：.qys 文件解析和导入逻辑
├── utils/
│   ├── crypto.py           # 复用 Story 3.3
│   └── storage.py          # 复用 Story 3.5
├── models.py               # 扩展 Strategy 模型字段
frontend/src/
├── views/
│   └── StrategyLibrary.vue # 新建：策略库管理页
└── components/
    └── strategy/
        ├── StrategyCard.vue    # 新建：策略卡片
        └── StrategyImport.vue  # 新建：拖拽上传组件
```

### 测试标准

- .qys 解析测试使用项目中的示例策略包（`docs/strategy-format/examples/`）
- API 测试覆盖权限校验（不能操作他人策略）
- 上传测试覆盖文件大小限制、格式错误、校验失败等边界情况

### 关键技术细节

**.qys 文件解析流程：**
```python
import tarfile, json, hashlib

def parse_qys(file_stream):
    with tarfile.open(fileobj=file_stream, mode='r:gz') as tar:
        # 1. 提取 strategy.json
        strategy_json = json.load(tar.extractfile('strategy.json'))
        # 2. 提取 src/strategy.py
        strategy_code = tar.extractfile('src/strategy.py').read()
        # 3. SHA256 校验
        file_hash = hashlib.sha256(file_stream.read()).hexdigest()
        if file_hash != strategy_json.get('checksum'):
            raise IntegrityError("文件完整性校验失败")
    return strategy_json, strategy_code
```

**Strategy 模型扩展字段：**
- title VARCHAR(200)
- description TEXT
- tags TEXT[] (PostgreSQL 数组)
- category ENUM('trend-following','mean-reversion','momentum','multi-indicator','other')
- is_public BOOLEAN DEFAULT false
- code_encrypted BYTEA (Story 3.3)
- code_hash VARCHAR(64) (Story 3.3)
- storage_key TEXT
- author_id → users.id (FK)

**依赖关系：**
- 依赖 Story 3.3（AES-256-GCM 加密 crypto.py）
- 依赖 Story 3.5（对象存储 storage.py）
- 被 Story 3.8（参数配置器，导入后跳转）依赖

### Project Structure Notes

- 策略导入逻辑独立为 `strategy_import.py` 服务，不放蓝图中
- Strategy 模型字段扩展需要 Alembic 迁移
- 前端拖拽上传使用 HTML5 Drag and Drop API 或 vue-upload 组件
- .qys 文件解析可以复用 `packages/qysp` 中的验证逻辑

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#领域4：策略代码加密存储（NFR10-11）] — 加密方案和 strategies 表扩展
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7] — 用户故事和验收标准
- [Source: packages/qysp/src/qysp/validator.py] — QYSP 验证器（可复用）
- [Source: backend/app/blueprints/strategies.py] — 现有策略蓝图
- [Source: backend/app/models.py#Strategy] — 现有 Strategy 模型
- [Source: docs/strategy-format/] — .qys 格式规范和示例

## Dev Agent Record

### Agent Model Used

<!-- 由 dev-story 执行时填写 -->

### Debug Log References

### Completion Notes List

### File List
