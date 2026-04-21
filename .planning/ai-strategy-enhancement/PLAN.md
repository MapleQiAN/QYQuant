# AI 策略生成增强 — 实现计划

## 目标

将 AI 策略生成从"裸聊天框"升级为"策略领航员"体验：
1. AI 对话后生成专业策略包（含策略报告、参数、完整代码）
2. 新增策略预览与编辑页（报告 + 参数编辑 + 代码预览 + 导出）
3. 前端流程从"聊天→跳过"变为"聊天→预览→编辑→导出/保存"

---

## Phase 1: 后端 — 增强 AI 策略生成

### 1.1 重写 system prompt

**文件**: `backend/app/services/ai_strategy_generation.py` → `_system_prompt()`

现状：只要求生成 `on_bar` 函数 + 简单 JSON schema。

改为要求输出完整策略包：

```json
{
  "reply": "助手回复文本",
  "strategy": {
    "name": "...",
    "description": "策略描述（专业、详细）",
    "category": "trend-following|mean-reversion|momentum|multi-indicator|other",
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "version": "1.0.0",
    "tags": ["..."],

    "logicExplanation": "大白话描述策略逻辑，给小白看的",
    "riskRules": "大白话描述风控规则",
    "suitableMarket": "适合什么行情（如：单边上涨、震荡市）",
    "riskLevel": "low|medium|high",

    "parameters": [
      {
        "key": "rsi_period",
        "type": "integer",
        "default": 14,
        "min": 5,
        "max": 50,
        "step": 1,
        "description": "RSI 计算周期",
        "user_facing": {
          "label": "RSI 周期",
          "group": "指标参数",
          "hint": "值越大信号越平滑，反应越慢"
        }
      }
    ],

    "code": "完整 Python 策略代码，带分段注释（信号、风控、仓位、执行）"
  }
}
```

**prompt 增强要点**：
- 必须包含风控逻辑（止损、止盈、仓位控制）
- 代码必须分段注释：`# === 信号检测 ===`、`# === 风控规则 ===`、`# === 仓位管理 ===`、`# === 执行下单 ===`
- 所有可调参数必须通过 `ctx.parameters.get()` 读取
- `logicExplanation` 和 `riskRules` 用中文大白话写
- `user_facing` 每个参数必须有 `label`、`group`、`hint`

### 1.2 扩展响应解析

**文件**: `backend/app/services/ai_strategy_generation.py` → `_normalize_strategy_payload()`

新增字段处理：
- `timeframe` → 存入 `metadataCandidates`
- `riskLevel` → 存入 `metadataCandidates`
- `logicExplanation` → 存入 `metadataCandidates`
- `riskRules` → 存入 `metadataCandidates`
- `suitableMarket` → 存入 `metadataCandidates`
- 参数的 `user_facing` 字段透传

`AiStrategyDraftResult` 的 analysis 中 `metadataCandidates` 会自动包含这些新字段。

### 1.3 新增导出 API

**文件**: `backend/app/blueprints/strategies.py`

新增路由：`GET /api/v1/strategy-ai/export`

```python
@bp.post("/v1/strategy-ai/export")
@jwt_required()
def export_strategy():
    """从 AI 生成的 draft 导出为 .qys 或 .py 文件"""
    payload = request.get_json() or {}
    draft_import_id = payload.get("draftImportId")
    format = payload.get("format", "qys")  # "qys" | "py"

    # 1. 从 sessionStorage 对应的 draft 中取代码和参数
    # 2. 如果 format == "py"，直接返回 Python 文件
    # 3. 如果 format == "qys"，构建完整 .qys 包：
    #    - strategy.json (完整 manifest)
    #    - src/strategy.py (策略代码)
    #    - README.md (策略报告 Markdown)
    #    调用 qysp.builder.build_package() 打包
    # 4. 返回文件下载
```

**实现逻辑**：
- 从 `StrategyImportDraft` 取 source_file
- 用 `_resolve_source_and_manifest()` 获取代码
- 用 `_build_manifest()` 构建 manifest（复用 `strategy_import_confirm.py` 的逻辑）
- 构建临时项目目录，调用 `build_package()` 生成 .qys
- 返回 `send_file()` 下载响应

### 1.4 修改点汇总

| 文件 | 操作 |
|------|------|
| `backend/app/services/ai_strategy_generation.py` | 重写 `_system_prompt()`、扩展 `_normalize_strategy_payload()` |
| `backend/app/blueprints/strategies.py` | 新增 `export_strategy` 路由 |

---

## Phase 2: 前端 — 类型与 API 层

### 2.1 扩展 TypeScript 类型

**文件**: `frontend/src/types/Strategy.ts`

```typescript
// AiStrategyDraftResult 的 analysis.metadataCandidates 中新增字段
export interface AiStrategyMetadata {
  name: string
  description: string
  category: string
  symbol: string
  timeframe?: string
  riskLevel?: 'low' | 'medium' | 'high'
  logicExplanation?: string
  riskRules?: string
  suitableMarket?: string
  version?: string
  tags?: string[]
}

// 扩展 StrategyParameter 的 user_facing
export interface StrategyParameterUserFacing {
  label: string
  group: string
  hint?: string
}
```

### 2.2 新增 API 函数

**文件**: `frontend/src/api/strategies.ts`

```typescript
export function exportStrategy(payload: {
  draftImportId: string
  format: 'qys' | 'py'
  metadata?: Record<string, unknown>
  parameterDefinitions?: StrategyParameter[]
}): Promise<Blob> {
  return client.request({
    method: 'post',
    url: '/v1/strategy-ai/export',
    data: payload,
    responseType: 'blob',
  })
}
```

### 2.3 修改点汇总

| 文件 | 操作 |
|------|------|
| `frontend/src/types/Strategy.ts` | 新增 `AiStrategyMetadata`、`StrategyParameterUserFacing` 接口 |
| `frontend/src/api/strategies.ts` | 新增 `exportStrategy()` |

---

## Phase 3: 前端 — 策略预览与编辑页

### 3.1 新增路由

**文件**: `frontend/src/router/index.ts`

```typescript
{
  path: '/strategies/preview',
  name: 'strategy-preview',
  component: () => import('../views/StrategyPreviewView.vue')
}
```

### 3.2 新建 StrategyPreviewView.vue

**文件**: `frontend/src/views/StrategyPreviewView.vue` (新建)

页面布局（四区布局）：

```
┌──────────────────────────────────────────────────────┐
│ 顶部栏：策略名称 + 返回按钮 + 操作按钮组             │
│ [导出 .qys] [导出 .py] [保存到我的策略]               │
├──────────────────────┬───────────────────────────────┤
│ 左侧面板            │ 右侧面板（Tab 切换）           │
│                      │                               │
│ ┌──────────────────┐ │ [策略报告] [代码] [参数详情]   │
│ │ 策略报告卡片      │ │                               │
│ │                  │ │ === Tab: 策略报告 ===          │
│ │ 【策略逻辑】      │ │ （完整策略文档，大白话）       │
│ │ 【风控规则】      │ │                               │
│ │ 【适合行情】      │ │ === Tab: 代码 ===              │
│ │ 【风险等级】      │ │ （语法高亮的 Python 代码）     │
│ └──────────────────┘ │                               │
│                      │ === Tab: 参数详情 ===           │
│ ┌──────────────────┐ │ （参数完整信息表格）           │
│ │ 参数编辑面板      │ │                               │
│ │ [参数组1]         │ │                               │
│ │  RSI周期 [14]  ↔  │ │                               │
│ │  超卖阈值 [30] ↔  │ │                               │
│ │ [参数组2]         │ │                               │
│ │  止损 [2%]    ↔  │ │                               │
│ │  止盈 [4%]    ↔  │ │                               │
│ └──────────────────┘ │                               │
├──────────────────────┴───────────────────────────────┤
│ 底部：AI 优化建议（快捷按钮）                         │
│ [放宽止损] [增加过滤条件] [调整仓位] [重新生成]       │
└──────────────────────────────────────────────────────┘
```

**数据来源**：从 `sessionStorage` 读取 `strategy-import:{draftImportId}`，包含完整的 analysis 和 metadataCandidates。

**核心功能**：

1. **策略报告**：展示 `logicExplanation`、`riskRules`、`suitableMarket`、`riskLevel`
2. **参数编辑**：复用 `ParameterForm.vue` 的模式，按 `user_facing.group` 分组，每个参数显示 `hint`
3. **代码预览**：Python 代码语法高亮显示，带复制按钮
4. **导出 .qys/.py**：调用 `exportStrategy()` API 下载文件
5. **保存到我的策略**：调用现有 `confirmStrategyImport()` 走原有流程

### 3.3 新建组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `StrategyReportCard.vue` | `frontend/src/components/strategy/StrategyReportCard.vue` | 策略报告卡片（逻辑、风控、适合行情） |
| `StrategyCodePreview.vue` | `frontend/src/components/strategy/StrategyCodePreview.vue` | Python 代码预览 + 复制 |
| `StrategyExportPanel.vue` | `frontend/src/components/strategy/StrategyExportPanel.vue` | 导出按钮组 (.qys/.py) |
| `AiSuggestionBar.vue` | `frontend/src/components/strategy/AiSuggestionBar.vue` | AI 优化建议快捷按钮 |

### 3.4 修改 AI 对话流程

**文件**: `frontend/src/views/NewStrategyView.vue`

改动：
1. `adoptAiDraft()` 不再跳转到 `strategy-import-confirm`，改为跳转到 `strategy-preview`
2. 修改 AI 卡片的 badge，从普通样式改为高亮"推荐"样式
3. AI 卡片排序提到第一位

```typescript
// 改前
await router.push({ name: 'strategy-import-confirm', query: { draftImportId: ..., source: 'ai' } })

// 改后
await router.push({ name: 'strategy-preview', query: { draftImportId: ..., source: 'ai' } })
```

### 3.5 修改点汇总

| 文件 | 操作 |
|------|------|
| `frontend/src/router/index.ts` | 新增 `strategy-preview` 路由 |
| `frontend/src/views/StrategyPreviewView.vue` | **新建** — 策略预览与编辑页 |
| `frontend/src/components/strategy/StrategyReportCard.vue` | **新建** — 策略报告卡片 |
| `frontend/src/components/strategy/StrategyCodePreview.vue` | **新建** — 代码预览 |
| `frontend/src/components/strategy/StrategyExportPanel.vue` | **新建** — 导出面板 |
| `frontend/src/components/strategy/AiSuggestionBar.vue` | **新建** — AI 优化建议 |
| `frontend/src/views/NewStrategyView.vue` | 改 `adoptAiDraft()` 跳转目标 + 调整卡片排序 |

---

## Phase 4: i18n 补充

### 4.1 新增多语言文案

需要在 `frontend/src/i18n/` 的各语言文件中补充：

- 策略预览页标题、Tab 标签
- 报告区块标签（策略逻辑、风控规则、适合行情、风险等级）
- 参数组标签
- 导出按钮文案
- AI 优化建议按钮文案

---

## 实现顺序

```
Phase 1 (后端)                    Phase 2 (前端类型/API)
┌─────────────────────────┐      ┌─────────────────────────┐
│ 1.1 重写 system prompt  │      │ 2.1 扩展 TS 类型        │
│ 1.2 扩展响应解析        │      │ 2.2 新增 API 函数       │
│ 1.3 新增导出 API        │      └─────────────────────────┘
└─────────────────────────┘                  │
         │                                   │
         └───────────┬───────────────────────┘
                     ▼
           Phase 3 (前端页面)
           ┌─────────────────────────┐
           │ 3.1 新增路由            │
           │ 3.2 新建预览页          │
           │ 3.3 新建组件            │
           │ 3.4 修改对话流程        │
           └─────────────────────────┘
                     │
                     ▼
           Phase 4 (i18n)
           ┌─────────────────────────┐
           │ 4.1 多语言文案          │
           └─────────────────────────┘
```

## 文件变更清单

| 操作 | 文件路径 |
|------|---------|
| **修改** | `backend/app/services/ai_strategy_generation.py` |
| **修改** | `backend/app/blueprints/strategies.py` |
| **修改** | `frontend/src/types/Strategy.ts` |
| **修改** | `frontend/src/api/strategies.ts` |
| **修改** | `frontend/src/router/index.ts` |
| **修改** | `frontend/src/views/NewStrategyView.vue` |
| **新建** | `frontend/src/views/StrategyPreviewView.vue` |
| **新建** | `frontend/src/components/strategy/StrategyReportCard.vue` |
| **新建** | `frontend/src/components/strategy/StrategyCodePreview.vue` |
| **新建** | `frontend/src/components/strategy/StrategyExportPanel.vue` |
| **新建** | `frontend/src/components/strategy/AiSuggestionBar.vue` |
| **修改** | `frontend/src/i18n/zh.json` |
| **修改** | `frontend/src/i18n/en.json` |

总计：**4 个修改 + 5 个新建 = 13 个文件**

## 不做的事

- 不改动现有导入确认流程（`StrategyImportConfirmView.vue` 保持不变，模板/文件导入继续走这个）
- 不改动后端 `strategy_import_confirm.py`（复用其逻辑用于导出，但不修改）
- 不增加数据库 migration（使用现有 `StrategyImportDraft` 和 `metadataCandidates` JSON 字段）
- 不引入新的前端依赖（代码高亮用 CSS + 简单 tokenizer，不引入 heavy library）
