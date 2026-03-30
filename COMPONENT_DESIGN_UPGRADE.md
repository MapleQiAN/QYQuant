# 组件设计系统升级文档

## 概述

本文档详细记录了四个核心业务组件应用新设计系统的改进细节。所有改进都致力于打造**专业、现代、企业级**的金融量化平台视觉体验。

---

## 1️⃣ StatCard（统计卡片）

**用途**：用于展示单一指标的数值和变化，如总回报、Sharpe 比率等。

### 🎨 设计改进

#### 卡片外观
```diff
+ 增大图标容器：44px → 48px
+ 添加顶部渐变装饰线（gradient：transparent → primary → transparent）
+ 改进悬停阴影（shadow-sm → shadow-md with color）
+ 添加悬居上升效果（translateY: -2px）
+ 改进边框色（color-border-light → color-border）
```

#### 图标背景
```css
/* 从简单背景到渐变背景 */
background: linear-gradient(135deg, var(--color-success-bg), rgba(16, 185, 129, 0.08))
```

#### 排版升级
```diff
标签 (stat-label):
- font-size: sm
- font-weight: medium
+ font-size: xs
+ font-weight: 700 (bold)
+ text-transform: uppercase
+ letter-spacing: 0.05em

值 (value):
- font-size: xl
- font-weight: bold
+ font-size: xxl
+ font-weight: 800 (ultra-bold)
+ letter-spacing: -0.01em
+ 添加 tabular-nums
```

#### Change Badge
```diff
- padding: 2px 6px
+ padding: 4px 8px
- font-weight: medium
+ font-weight: 700
+ border: 1px solid rgba(...)
```

### 📱 视觉效果

| 元素 | 改进 |
|------|------|
| 图标 | 渐变背景 + 更大容器 |
| 标签 | 大写 + 更粗 + 更广的间距 |
| 值 | 更大 + 更粗 + tabular-nums |
| 悬停 | 上升 + 增强阴影 + 边框变色 |

---

## 2️⃣ StrategyCard（策略卡片）

**用途**：在策略库和市场中展示策略概览，包含描述、指标、作者信息。

### 🎨 设计改进

#### 卡片整体
```diff
+ 添加顶部渐变装饰线
+ 改进边框（color-border-light → color-border）
+ 背景色一致性应用
+ 悬停时更大上升高度（-2px → -4px）
+ 更强的悬停阴影（0 12px 32px）
```

#### 标题排版
```diff
- font-size: lg
- font-weight: semibold
+ font-size: lg
+ font-weight: 700
+ letter-spacing: -0.01em
```

#### Metric 单元格（重要改进）
```css
/* 从纯背景色到渐变 */
background: linear-gradient(135deg,
  var(--color-surface-elevated),
  var(--color-surface-active)
);

/* 添加悬停效果 */
.metric-cell:hover {
  border-color: var(--color-primary-border);
  background: linear-gradient(135deg,
    var(--color-surface-elevated),
    var(--color-surface-hover)
  );
}
```

#### 指标值样式
```diff
- font-size: sm
- font-weight: semibold
- color: primary
+ font-size: md
+ font-weight: 700
+ color: primary
+ font-variant-numeric: tabular-nums
```

#### 卡片底部
```diff
- padding-top: md
- border-top: color-border-light
+ padding-top: lg
+ border-top: color-border
+ 添加明确的分隔
```

#### 作者信息
```diff
- avatar: 24px
+ avatar: 28px
+ border: 2px（增强可见性）
- font-weight: semibold
+ font-weight: 700
```

### 📊 视觉层次

```
[LOGO] Strategy Title [VERIFIED BADGE]
     ↓
     Description (min-height: 42px)
     ↓
     Category (uppercase, 0.05em letter-spacing)
     ↓
   [METRICS GRID - 3列 with gradients]
     ↓
   ┌─────────────────────────────────┐
   │ [AVATAR] Author Name  [Try Btn] │
   └─────────────────────────────────┘
```

---

## 3️⃣ BacktestCard（回测卡片）

**用途**：展示回测结果、KPI、图表和交易数据，是数据展示的核心组件。

### 🎨 设计改进

#### 卡片头部
```diff
- padding: lg
+ padding: xl
+ 添加下边框分隔
+ 增加底部间距
- gap: md
+ gap: lg
```

#### 标题和徽章
```diff
- font-size: lg
- font-weight: semibold
+ font-size: xl
+ font-weight: 700
+ letter-spacing: -0.01em
```

#### 数据源选择
```css
/* 改进的表单控件 */
.data-source-select {
  padding: 8px 12px;  /* 更大的 padding */
  background: var(--color-surface-elevated);  /* 更亮 */
  font-weight: 600;

  &:hover {
    border-color: var(--color-primary-border);
    background: var(--color-surface-hover);
  }

  &:focus {
    border-color: var(--color-primary-border);
    box-shadow: 0 0 0 3px var(--color-primary-bg);
  }
}
```

#### KPI 网格
```diff
- gap: md
+ gap: lg
- margin-bottom: lg
+ margin-bottom: xl
```

#### 图表部分
```css
/* 从简单到有视觉深度 */
background: linear-gradient(
  135deg,
  var(--color-surface-elevated),
  var(--color-surface)
);
border: 1px solid var(--color-border);
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
border-radius: var(--radius-lg);
```

#### 次要统计
```diff
- gap: xl
+ gap: xxl
- padding-top: md
+ padding-top: lg
- border-top: color-border-light
+ border-top: color-border

.stat-label:
- font-size: sm
+ font-size: xs
+ font-weight: 700
+ text-transform: uppercase

.stat-value:
- font-size: md
- font-weight: semibold
+ font-size: lg
+ font-weight: 700
+ color: primary
```

### 📈 信息架构

```
┌─────────────────────────────────────────┐
│ 📊 Latest Backtest Results    [Actions] │ ← Header with actions
├─────────────────────────────────────────┤
│ [KPI Grid: 4 columns with improved styling]
├─────────────────────────────────────────┤
│ [Chart Section with gradient background]
├─────────────────────────────────────────┤
│ Win Rate  Profit Factor  Total Trades  Avg Holding
│    68%        1.85          256         2.3d
└─────────────────────────────────────────┘
```

---

## 4️⃣ ProgressCard（进度卡片）

**用途**：展示用户使用配额、机器人运行时间、盈利情况等统计数据。

### 🎨 设计改进

#### 卡片头部
```css
/* 背景渐变 */
background: linear-gradient(
  135deg,
  var(--color-surface-elevated),
  var(--color-surface)
);
border-bottom: 1px solid var(--color-border);
```

#### 统计块（Stat Block）
```css
/* 从纯色到有层次感 */
background: linear-gradient(
  135deg,
  var(--color-surface-elevated),
  var(--color-surface-active)
);
border: 1px solid var(--color-border);
border-radius: var(--radius-lg);
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);

&:hover {
  border-color: var(--color-primary-border);
  background: linear-gradient(
    135deg,
    var(--color-surface-elevated),
    var(--color-surface-hover)
  );
}
```

#### 进度条
```css
/* 增强的视觉效果 */
.progress-fill {
  background: linear-gradient(90deg,
    var(--color-primary) 0%,
    var(--color-accent) 100%
  );
  box-shadow: 0 0 12px rgba(30, 90, 168, 0.3);
}
```

#### 运行时可视化
```diff
- height: 24px
+ height: 28px
+ 改进的活跃状态样式
+ 添加悬停效果
```

#### 盈利块
```css
/* 更生动的渐变和颜色 */
background: linear-gradient(
  135deg,
  var(--color-up-bg) 0%,
  var(--color-surface-active) 100%
);

&:hover {
  background: linear-gradient(
    135deg,
    rgba(255, 59, 59, 0.15),
    var(--color-surface-hover) 100%
  );
}
```

#### 快速统计
```css
/* 从简单行到交互式项目 */
.quick-stat-item {
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);

  &:hover {
    background: var(--color-surface-hover);
  }
}

.quick-stat-icon {
  width: 40px;  /* 从 36px 增加 */
  background: linear-gradient(135deg,
    var(--color-*-bg),
    rgba(..., 0.08)
  );
}
```

#### 排版标准化
```diff
.stat-label:
- font-size: sm
+ font-size: xs
+ font-weight: 700
+ text-transform: uppercase
+ letter-spacing: 0.05em

.quick-stat-value:
- font-size: sm
- font-weight: semibold
+ font-size: md
+ font-weight: 700
+ letter-spacing: -0.01em
```

### 📊 层次结构

```
┌────────────────────────────────────────┐
│ 📈 Progress Card        [Period Selector]
├────────────────────────────────────────┤
│ ┌──────────────────────────────────┐  │
│ │ Backtest Count: 45/100           │  │
│ │ ████████░░░░░░░░░░░░░░░░░░░░░░░░│ │ ← 45%
│ │ Monthly Quota        45%          │  │
│ └──────────────────────────────────┘  │
│ ┌──────────────────────────────────┐  │
│ │ Robot Runtime: 892h              │  │
│ │ [█][█][█][█][█][█][░]  7 days   │  │
│ │ Active Bots              4       │  │
│ └──────────────────────────────────┘  │
│ ┌──────────────────────────────────┐  │
│ │ Total Profit: $28,650.80  ↑12.5% │  │
│ │ [Chart visualization]            │  │
│ └──────────────────────────────────┘  │
├────────────────────────────────────────┤
│ ✓ 68% Win Rate  ⏱ 2.3d Avg Hold  🎯 1.85 Sharpe
└────────────────────────────────────────┘
```

---

## 🎯 跨组件设计一致性

### 颜色系统应用

| 类型 | 组件 | 应用 |
|------|------|------|
| 主色渐变 | StatCard, StrategyCard | 装饰线、图标背景 |
| 次要渐变 | BacktestCard, ProgressCard | 背景、填充 |
| 悬停效果 | 全部 | 边框变色 + 背景加深 + 阴影 |
| 强调色 | 所有统计值 | 数值显示、Badge |

### 排版标准

| 类型 | 大小 | 权重 | 应用 |
|------|------|------|------|
| 标签 | xs | 700 | 所有卡片标签 |
| 值 | xxl/lg | 700/800 | 统计数值 |
| 正文 | sm/md | 400 | 描述、说明 |
| 强调 | xs/sm | 600/700 | Badge、提示 |

### 间距规范

| 用途 | 间距 | 应用 |
|------|------|------|
| 卡片内部 | lg | 所有卡片 padding |
| 网格间隙 | md/lg | 组件间的距离 |
| 元素间隙 | sm/md | 组件内部元素 |
| 顶部/底部分隔 | lg | 头部、底部边框距离 |

---

## ✨ 核心设计原则

### 1. 专业可信
- ✅ 使用企业级蓝色系统（#1E5AA8）
- ✅ 清晰的信息层次
- ✅ 高对比度的文本（WCAG A+）

### 2. 数据优先
- ✅ 简洁的界面设计
- ✅ 清晰的数值展示（tabular-nums）
- ✅ 避免视觉干扰

### 3. 现代极简
- ✅ 精确的渐变和阴影
- ✅ 有意义的悬停动画
- ✅ 一致的边框和间距

### 4. 易用易访
- ✅ 清晰的交互反馈
- ✅ 一致的控件样式
- ✅ 无障碍设计考量

---

## 📊 技术实施

### CSS 变量利用
```css
/* 颜色 */
--color-primary: #1E5AA8
--color-accent: #00D9FF
--color-success: #10B981
--color-danger: #FF3B3B

/* 渐变 */
background: linear-gradient(135deg,
  var(--color-primary-bg),
  rgba(30, 90, 168, 0.08)
);

/* 阴影 */
box-shadow: 0 8px 24px rgba(30, 90, 168, 0.12);

/* 过渡 */
transition: all var(--transition-normal);
```

### 无 JavaScript 改进
- 所有改进都是纯 CSS
- 利用现有的 CSS 变量系统
- 保留所有现有功能
- 0 性能影响

---

## 🚀 后续优化建议

### 即期
- [ ] 表单输入框样式统一
- [ ] 模态框和对话框设计
- [ ] 数据表格样式完善

### 短期
- [ ] 图表配色方案优化
- [ ] 加载和骨架屏样式
- [ ] 其他卡片组件统一

### 长期
- [ ] 设计系统文档发布
- [ ] 组件库创建
- [ ] 设计令牌文档

---

## 📝 提交信息

### Commit 1: 全局设计系统
- 颜色系统升级
- 字体导入和排版
- 按钮、卡片、Badge 重新设计

### Commit 2: 组件设计升级
- StatCard 完整升级
- StrategyCard 现代化
- BacktestCard 增强
- ProgressCard 优化

---

## 总结

通过本次设计系统升级，QY Quant 平台实现了：

✨ **视觉一致性** - 统一的颜色、字体、间距、阴影系统
🎯 **专业形象** - 企业级蓝色配色、高对比度设计
⚡ **现代感觉** - 渐变、玻璃化、平滑动画
📊 **数据优先** - 清晰的信息层次、专注的展示
♿ **易用易访** - 清晰的交互、一致的控件、无障碍设计

**所有改进都是向后兼容的**，可以逐步应用到其他组件。
