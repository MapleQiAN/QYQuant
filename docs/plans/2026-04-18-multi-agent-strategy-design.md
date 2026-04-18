# QYQuant 策略生成系统设计

> 日期: 2026-04-18
> 状态: 设计确认，待实施
> 核心问题: 小白用户面对MA1/ATR/止损等专业参数直接流失（"参数坟场"问题）

## 1. 设计目标

**一句话**: 用户用自然语言描述交易想法，系统生成可执行策略代码。

**三原则**:
- **零强制**: 不强制走AI，专业用户可直出参数面板
- **零开销**: 专业模式不加载Agent、不调LLM
- **随时切换**: 引导模式和专家模式可自由切换

## 2. 三条用户路径

```
┌──────────────────────────────────────────────────────┐
│                    用户选择入口                       │
│                                                      │
│   ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│   │ 引导模式   │  │ 混合模式   │  │ 专业模式     │  │
│   │ (纯Layer1) │  │ (1↔2切换) │  │ (纯Layer2)   │  │
│   └─────┬──────┘  └─────┬──────┘  └──────┬───────┘  │
│    小白用户         成长型用户         专业用户      │
│    全程AI引导       先AI后手动         直接改参数    │
└─────────┼───────────────┼────────────────┼───────────┘
          │               │                │
          ▼               ▼                ▼
   Generator流程    Generator + 手动  现有参数面板
```

## 3. 架构总览

**1个Agent + 4个函数 + 1个搜索算法。**

| 组件 | 类型 | 本质 |
|------|------|------|
| Strategy Generator | **Agent** | 有LLM迭代循环、状态管理、降级决策 |
| classify_intent() | 函数 | 单次LLM调用，分类5个策略方向 |
| build_risk_profile() | 函数 | 表单数据→结构化画像 |
| generate_user_facing() | 函数 | 单次LLM调用+缓存 |
| format_summary() | 函数 | 格式化策略说明展示 |
| optimize() | 搜索算法 | 网格/贝叶斯参数搜索+过拟合检测 |

## 4. Strategy Generator Agent（唯一Agent）

用户描述需求 → 生成符合qysp规范的策略代码。

### 4.1 输入/输出

```typescript
interface GenerationRequest {
  user_description: string    // 自然语言描述
  risk_profile: RiskProfile   // 风险画像
  symbol?: string             // 可选：交易标的
  timeframe?: string          // 可选：时间框架
}

interface GenerationResult {
  code: string                // 策略Python代码
  parameters: ParamDef[]      // 参数定义（含user_facing）
  explanation: string         // 自然语言解释策略逻辑
}
```

### 4.2 Prompt架构

```
System Prompt:
  - 你是量化策略代码生成器
  - 只能输出符合 qysp 规范的代码
  - 禁止使用未列出的API

API Reference (注入qysp文档):
  - indicators.py 可用函数清单
  - context.py 接口说明
  - parameters.py 参数定义规范
  - 4个模板示例代码

User Input:
  - 用户需求描述
  - 风险画像
  - 标的/时间范围
```

### 4.3 校验管线

```python
def validate_generated_strategy(code: str) -> ValidationResult:
    # Step 1: AST安全检查
    #   禁止: import os/sys, open(), exec(), eval(), __import__
    #   禁止: 网络调用, 文件操作, 子进程

    # Step 2: qysp规范校验
    #   必须: 使用 qysp.context 的 Context
    #   必须: 定义 on_bar() 或 on_tick()
    #   必须: 通过 ctx.buy() / ctx.sell() 下单

    # Step 3: 参数定义校验
    #   必须: parameters 列表格式正确
    #   必须: 每个 parameter 有 key/type/min/max

    # Step 4: 沙箱导入测试
    #   在隔离环境中 import，确认无运行时错误

    # Step 5: 样本运行
    #   用30天数据快速跑一次，确认不崩溃
```

### 4.4 迭代循环

```
生成 → 校验失败？
  ├── AST违规 → 错误提示 → 重新生成
  ├── 规范不符 → 具体缺失 → 重新生成
  ├── 运行时错误 → traceback → 修复
  └── 崩溃 → 上下文信息 → 修复

最多3轮自动修复。3轮不过 → 降级到模板组装。
```

### 4.5 安全边界

```python
ALLOWED_IMPORTS = {"qysp.context", "qysp.indicators", "qysp.parameters", "math"}
ALLOWED_BUILTINS = {"len", "range", "min", "max", "abs", "round", "sum", "sorted"}
BLOCKED_NODES = {Import, Exec, Eval}

# 沙箱限制:
# - 无网络
# - 无文件系统
# - 内存限制 128MB
# - CPU时间限制 30s
```

### 4.6 生成示例

**用户输入**: "我想在黄金上做一个RSI超卖反弹策略，RSI低于30买入，高于70卖出，每次只用20%资金"

**Agent输出**:
```python
from qysp.context import Context
from qysp.indicators import rsi

parameters = [
    {"key": "rsi_period", "type": "integer", "min": 5, "max": 30, "default": 14,
     "label": "RSI周期", "user_facing": {
         "question": "RSI灵敏度？",
         "options": [
             {"label": "灵敏", "value": 7},
             {"label": "标准", "value": 14},
             {"label": "平滑", "value": 21}
         ]
     }},
    {"key": "oversold", "type": "number", "min": 10, "max": 40, "default": 30,
     "label": "超卖阈值"},
    {"key": "overbought", "type": "number", "min": 60, "max": 90, "default": 70,
     "label": "超买阈值"},
    {"key": "position_pct", "type": "number", "min": 0.05, "max": 1.0, "default": 0.2,
     "label": "每次仓位比例"},
]

def on_bar(ctx: Context):
    rsi_val = rsi(ctx.close, period=ctx.params.rsi_period)

    if rsi_val < ctx.params.oversold and not ctx.has_position:
        qty = int(ctx.cash * ctx.params.position_pct / ctx.close)
        if qty > 0:
            ctx.buy(qty)

    elif rsi_val > ctx.params.overbought and ctx.has_position:
        ctx.sell(ctx.position_size)
```

---

## 5. 辅助函数

### 5.1 classify_intent() — 意图分类

单次LLM调用，输出直接喂给Strategy Generator。

```typescript
// 输入: 用户自然语言描述
// 输出:
interface IntentResult {
  strategy_type: "trend_following" | "mean_reversion" | "momentum" | "multi_indicator" | "custom"
  direction: "long" | "short" | "both"
  timeframe: "short" | "medium" | "long"
  confidence: number
}
```

映射表:
| 用户说法 | 映射 |
|---------|------|
| 抓上涨趋势、追涨、顺势 | trend_following |
| 低位反弹、抄底、超卖 | mean_reversion |
| 动量突破、放量、强势 | momentum |
| 多个指标结合、综合判断 | multi_indicator |
| 不属于以上任何一种 | custom（触发纯代码生成） |

### 5.2 build_risk_profile() — 风险画像

可视化控件直接输出结构化数据，末尾附"还有补充吗？"文本框走LLM解析。

```typescript
interface RiskProfile {
  max_single_loss_pct: number      // → stop_loss_ratio
  position_ratio: number            // → position_size
  drawdown_tolerance: "low" | "medium" | "high"
  consecutive_loss_patience: number // → 信号过滤强度
  style: "conservative" | "balanced" | "aggressive"
}
```

| 问题 | 控件类型 | 映射目标 |
|------|---------|---------|
| 单次最多接受亏多少？ | 滑块(1%-10%) | stop_loss_ratio |
| 同一时间愿意持仓几只？ | 选项(1/2/3/5) | position_sizing |
| 能接受连续几次判断错误？ | 选项(2/3/5/8) | 信号过滤强度 |
| 回撤到多少你会睡不着？ | 滑块(5%-30%) | max_drawdown_alert |
| 资金使用比例？ | 滑块(10%-100%) | position_ratio |

### 5.3 generate_user_facing() — 动态界面生成

策略加载时缺少 `user_facing` 定义时触发。单次LLM调用 + 结果缓存。

strategy.json parameters schema扩展:
```json
{
  "key": "atr_multiplier",
  "type": "number",
  "min": 0.5,
  "max": 5.0,
  "default": 2.0,
  "user_facing": {
    "question": "你能接受多大的单次波动？",
    "options": [
      { "label": "严格止损", "value": 1.0, "desc": "波动小就止损，保本优先" },
      { "label": "适度宽容", "value": 2.0, "desc": "给策略一些呼吸空间" },
      { "label": "宽松持有", "value": 3.5, "desc": "容忍较大波动，博更大收益" }
    ]
  }
}
```

内置4模板由开发者预设。用户上传策略:
- 作者定义了 user_facing → 直接用
- 没定义 → LLM自动生成 → 缓存

### 5.4 format_summary() — 策略摘要展示

校验通过后展示策略说明和参数列表（不跑轻量回测，校验管线Step 5已验证可运行）。

```
展示:
  策略说明：RSI超卖反弹，RSI<30买入，RSI>70卖出
  参数列表：RSI周期 / 超卖阈值 / 超买阈值 / 仓位比例
  用户操作：
  ├── 确认 → 跑完整回测
  ├── 修改参数 → 回到参数调整
  └── 重新生成 → 回到Strategy Generator
```

---

## 6. 优化算法 optimize()

纯算法，无LLM。在参数空间搜索更优组合。

### 分层搜索
```python
def optimize(strategy, params, risk_profile, level="standard"):
    search_space = build_search_space(params)

    if level == "quick":
        results = grid_search(strategy, search_space, n_points=3)
    elif level == "standard":
        coarse = grid_search(strategy, search_space, n_points=5)
        results = grid_search(strategy, narrow(coarse, top_10_pct), n_points=5)
    elif level == "deep":
        coarse = grid_search(...)
        refined = grid_search(...)
        results = bayesian_optimize(refined, n_iter=50)

    return detect_overfitting(top_n(results, n=3))
```

### 目标函数
```python
def objective(backtest_result, risk_profile):
    weights = {
        "conservative": {"return": 0.3, "drawdown": 0.5, "sharpe": 0.2},
        "balanced":     {"return": 0.4, "drawdown": 0.3, "sharpe": 0.3},
        "aggressive":   {"return": 0.6, "drawdown": 0.2, "sharpe": 0.2},
    }
```

### 过拟合检测
- 样本内/外 80/20 分割
- 过拟合信号: 样本内Top3在样本外排名跌出前50%
- 输出Top 3参数组合 + 过拟合风险标注

### 资源控制
| 级别 | 搜索轮次 | 并发 | 耗时 | 对应会员 |
|------|---------|------|------|---------|
| 快速 | 粗网格1轮 | 4 | ~30s | 免费 |
| 标准 | 粗+细 | 8 | ~2min | 轻量级/进阶 |
| 深度 | 粗+细+贝叶斯 | 16 | ~10min | 专业版 |

---

## 7. 完整数据流

```
用户自然语言描述
       │
       ▼
  classify_intent() → IntentResult
       │
       ▼
  build_risk_profile() → RiskProfile
       │
       ▼
  Strategy Generator (LLM + qysp)
       │ → 策略代码 + 参数定义(含user_facing)
       │ → 校验管线(AST/规范/沙箱/样本运行)
       │ → 不通过？自动修复(最多3轮)
       ▼
  format_summary() → 策略说明 + 参数列表
       │
       ▼
  用户操作：
  ├── 确认 → 跑完整回测
  ├── 修改参数 → 参数调整
  ├── 重新生成 → 回到Generator
  └── 优化 → optimize() → Top 3参数组合
```

## 8. 与现有代码的接入点

| 现有代码 | 接入方式 |
|---------|---------|
| `params.py` validate_and_merge_params() | Generator输出的参数必须通过此校验 |
| `packages/qysp/` SDK | Generator生成的代码必须符合qysp规范 |
| `validator.py` | 策略代码校验 |
| 4个策略模板 | classify_intent()的匹配池 + Generator的参考示例 |
| `StrategyParamsPanel.vue` | Layer 2专业界面，保持不变 |
| `quota_tasks.py` | optimize()的会员资源控制 |
| 回测引擎 | 完整回测 + optimize()共用 |

## 9. 风险与对策

| 风险 | 严重程度 | 对策 |
|------|---------|------|
| 生成代码有bug | 高 | qysp validator + 沙箱运行 + 3轮自动修复 |
| 策略亏损用户追责 | 高 | 免责声明 + 模拟盘优先 + 风险提示 |
| 代码注入攻击 | 高 | AST白名单 + 沙箱隔离(无网络/文件/子进程) |
| LLM幻觉(调用不存在的API) | 中 | qysp API文档注入prompt + 生成后校验 |
| 生成不稳定的策略 | 中 | 样本外验证 + 过拟合检测 |
| 3轮修复仍失败 | 中 | 降级到模板组装，不硬卡 |

## 10. Phase规划

### Phase 1: 基础设施
- strategy.json schema扩展(增加user_facing)
- AST安全检查器
- 沙箱执行环境
- qysp API文档提取(注入prompt用)

### Phase 2: Strategy Generator Agent
- Prompt工程(system prompt + API reference + 示例)
- 校验管线(AST→规范→参数→沙箱→样本运行)
- 迭代修复循环(最多3轮 + 降级)
- generate_user_facing()函数

### Phase 3: 辅助函数 + UI
- classify_intent()函数
- build_risk_profile()表单UI组件
- format_summary()展示组件
- 引导模式/混合模式/专业模式切换

### Phase 4: optimize()搜索算法
- 分层搜索(grid + bayesian)
- 过拟合检测
- 会员资源分级
