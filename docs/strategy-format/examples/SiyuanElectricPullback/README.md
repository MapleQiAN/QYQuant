# Siyuan Electric Pullback

思源电气 `002028.XSHE` 日线回测示例。

策略规则：

- 买入：前一日收盘仍在 10 日均线上方，今日最低价回踩到 10 日均线，且收盘重新站回 10 日均线
- 卖出：收盘跌破 30 日均线，或收盘触及 / 突破 Boll 上轨
- 仓位：默认使用 95% 可用现金

说明：

- 当前示例按 QYQuant 现有 A 股格式使用 `002028.XSHE`
- 如果你平时写 `sz002028`，导入到当前回测链路时建议统一成 `002028.XSHE`
- “回踩 10 日线”这里做了一个明确化假设：不是单纯收盘靠近，而是当日最低价真正触到 / 跌破 10 日线，并且收盘重新站上

构建：

```bash
uv run qys build docs/strategy-format/examples/SiyuanElectricPullback --output SiyuanElectricPullback.qys
```

校验：

```bash
uv run qys validate docs/strategy-format/examples/SiyuanElectricPullback
```
