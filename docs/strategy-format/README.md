# QY Strategy Package (QYSP) v1

本文定义 QYQuant 的统一策略文件格式，用于策略导入、导出、共享与长期存储。

**目标**
- 自描述：文件本身包含策略元数据、参数说明、依赖与运行入口。
- 可复现：同一包在不同环境可重建相同的回测与交易行为。
- 易共享：单文件 `.qys` 便于上传、下载和版本管理。
- 可扩展：通过 `schemaVersion` 与可选字段实现向后兼容。

**文件格式**
- 统一扩展名：`.qys`
- 实体格式：ZIP 压缩包，UTF-8 文本
- 必含文件：`strategy.json`（清单）
- 推荐目录结构：

```text
my-strategy.qys
├─ strategy.json
├─ src/
│  └─ strategy.py
├─ requirements.txt
├─ README.md
└─ assets/
   └─ logo.png
```

**strategy.json 结构**
`strategy.json` 是唯一强制文件，用于导入、索引、存储与展示。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| schemaVersion | string | 是 | 清单版本，当前固定为 `1.0` |
| kind | string | 是 | 固定为 `QYStrategy` |
| id | string | 是 | 策略全局唯一 ID（UUID） |
| name | string | 是 | 策略名称 |
| version | string | 是 | 策略版本号（SemVer） |
| description | string | 否 | 策略简介 |
| language | string | 是 | 语言标识，例如 `python` |
| runtime | object | 是 | 运行环境声明 |
| entrypoint | object | 是 | 策略入口声明 |
| parameters | array | 否 | 参数定义列表 |
| universe | object | 否 | 交易标的与市场定义 |
| data | object | 否 | 数据频率与字段需求 |
| execution | object | 否 | 执行模型与费用假设 |
| risk | object | 否 | 风控约束 |
| tags | array | 否 | 标签列表 |
| author | object | 否 | 作者信息 |
| license | string | 否 | 许可证标识 |
| createdAt | string | 否 | ISO8601 日期时间 |
| updatedAt | string | 否 | ISO8601 日期时间 |
| performance | object | 否 | 回测摘要（可选） |
| dependencies | object | 否 | 依赖声明 |
| integrity | object | 否 | 文件校验信息 |

**runtime**
| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 运行时名称，例如 `python` |
| version | string | 是 | 运行时版本，例如 `3.11` |

**entrypoint**
| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| path | string | 是 | 入口文件路径，例如 `src/strategy.py` |
| callable | string | 是 | 入口对象名称，例如 `Strategy` 或 `main` |
| interface | string | 否 | 约定接口名，例如 `event_v1` |

**parameters**
每个参数对象支持以下字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| key | string | 是 | 参数键名 |
| type | string | 是 | `integer` `number` `string` `boolean` `enum` `array` `object` |
| default | any | 否 | 默认值 |
| required | boolean | 否 | 是否必填 |
| min | number | 否 | 数值最小值 |
| max | number | 否 | 数值最大值 |
| step | number | 否 | 步进 |
| enum | array | 否 | 枚举值列表 |
| description | string | 否 | 参数说明 |
| ui | object | 否 | UI 展示提示，例如 `{"widget":"slider"}` |

**universe**
推荐字段：`symbols`（数组）、`assetClass`、`market`、`currency`、`timezone`。

**data**
推荐字段：`resolution`（如 `1m` `1h` `1d`）、`fields`（OHLCV）、`lookback`（整数）。

**execution**
推荐字段：`orderTypes`、`slippageBps`、`commissionBps`、`priceType`、`maxOrdersPerDay`。

**risk**
推荐字段：`maxPositionPct`、`maxDrawdownPct`、`stopLossPct`、`takeProfitPct`、`cooldownDays`。

**dependencies**
- `pip`: Python 依赖列表
- `conda`: Conda 依赖列表

**integrity**
- `files`: `{path, sha256, size}` 列表，用于上传校验与去重

**导入与数据库映射建议**
- `strategies` 表字段映射：
`name` <- `name`
`symbol` <- `universe.symbols[0]`
`status` <- `draft` 或导入状态
`tags` <- `tags`
`last_update` <- `updatedAt`
- 版本表 `strategy_versions`：
`version` <- `version`
`file_id` <- 上传后的文件 ID
`checksum` <- `integrity.files[*].sha256` 合并或整体包哈希

**向后兼容约定**
- 仅允许新增可选字段
- 字段语义改变必须提升 `schemaVersion` 主版本

**最小可用示例**
见 `docs/strategy-format/examples/GoldTrend/strategy.json`。
