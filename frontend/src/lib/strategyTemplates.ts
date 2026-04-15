export interface StrategyTemplateDefinition {
  id: string
  slug: string
  nameKey: string
  descriptionKey: string
  filename: string
  defaultName: string
  defaultSymbol: string
  tags: string[]
  category: string
  code: string
}

export const strategyTemplates: StrategyTemplateDefinition[] = [
  {
    id: 'dual-ma',
    slug: 'dual-ma',
    nameKey: 'strategyNew.templates.dualMa.name',
    descriptionKey: 'strategyNew.templates.dualMa.description',
    filename: 'double-moving-average.py',
    defaultName: 'Double Moving Average',
    defaultSymbol: 'BTCUSDT',
    tags: ['template', 'trend'],
    category: 'trend-following',
    code: `from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    fast_period = int(ctx.parameters.get("fast_period", 5))
    slow_period = int(ctx.parameters.get("slow_period", 20))

    if fast_period >= slow_period:
        return []

    prices = list(getattr(ctx, "_dual_ma_prices", []))
    prices.append(float(data.close))
    prices = prices[-slow_period:]
    setattr(ctx, "_dual_ma_prices", prices)
    if len(prices) < slow_period:
        return []

    fast_ma = sum(prices[-fast_period:]) / fast_period
    slow_ma = sum(prices) / slow_period

    if fast_ma > slow_ma:
        return [ctx.buy(data.symbol, quantity=1)]
    return []
`,
  },
  {
    id: 'momentum',
    slug: 'momentum',
    nameKey: 'strategyNew.templates.momentum.name',
    descriptionKey: 'strategyNew.templates.momentum.description',
    filename: 'momentum-strategy.py',
    defaultName: 'Momentum Strategy',
    defaultSymbol: 'ETHUSDT',
    tags: ['template', 'momentum'],
    category: 'momentum',
    code: `from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    lookback = int(ctx.parameters.get("lookback", 10))
    prices = list(getattr(ctx, "_momentum_prices", []))
    prices.append(float(data.close))
    prices = prices[-lookback:]
    setattr(ctx, "_momentum_prices", prices)
    if len(prices) < lookback:
        return []

    if prices[-1] > prices[0]:
        return [ctx.buy(data.symbol, quantity=1)]
    return []
`,
  },
  {
    id: 'mean-reversion',
    slug: 'mean-reversion',
    nameKey: 'strategyNew.templates.meanReversion.name',
    descriptionKey: 'strategyNew.templates.meanReversion.description',
    filename: 'mean-reversion.py',
    defaultName: 'Mean Reversion',
    defaultSymbol: 'XAUUSD',
    tags: ['template', 'reversion'],
    category: 'mean-reversion',
    code: `from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    lookback = int(ctx.parameters.get("lookback", 20))
    threshold = float(ctx.parameters.get("threshold", 0.02))
    prices = list(getattr(ctx, "_mean_reversion_prices", []))
    prices.append(float(data.close))
    prices = prices[-lookback:]
    setattr(ctx, "_mean_reversion_prices", prices)
    if len(prices) < lookback:
        return []

    average_price = sum(prices) / len(prices)
    if average_price <= 0:
        return []

    deviation = (data.close - average_price) / average_price
    if deviation < -threshold:
        return [ctx.buy(data.symbol, quantity=1)]
    return []
`,
  },
  {
    id: 'blank',
    slug: 'blank',
    nameKey: 'strategyNew.templates.blank.name',
    descriptionKey: 'strategyNew.templates.blank.description',
    filename: 'blank-strategy.py',
    defaultName: 'Blank Strategy',
    defaultSymbol: 'BTCUSDT',
    tags: ['template', 'blank'],
    category: 'other',
    code: `from qysp import BarData, Order, StrategyContext


def on_bar(ctx: StrategyContext, data: BarData) -> list[Order]:
    return []
`,
  },
]
