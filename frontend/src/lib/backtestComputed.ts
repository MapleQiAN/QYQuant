import type { Trade } from '../types/Trade'
import type { BacktestReportPoint } from '../types/Backtest'

export interface SignalStats {
  buyCount: number
  sellCount: number
  buySellRatio: string
  buyWinRate: string
  sellWinRate: string
  avgBuyPnl: string
  avgSellPnl: string
  bestTrade: { pnl: number; index: number } | null
  worstTrade: { pnl: number; index: number } | null
  signalFrequencyDaily: string
  signalFrequencyWeekly: string
  avgHoldingPeriod: string
}

export interface BenchmarkComparison {
  benchmarkTotalReturn: number | null
  excessReturn: number | null
  trackingError: number | null
  informationRatio: number | null
}

export interface RiskMetrics {
  profitFactor: string
  expectancy: string
  maxConsecutiveWins: number
  valueAtRisk95: string
  avgWinningTrade: string
  avgLosingTrade: string
  varDisclaimer: boolean
}

export interface PnlBucket {
  range: string
  count: number
}

export interface DurationBucket {
  range: string
  count: number
}

export interface MonthlyReturn {
  month: string
  returnPct: number | null
}

export interface TradeDistribution {
  pnlHistogramBuckets: PnlBucket[]
  holdingDurationBuckets: DurationBucket[]
  monthlyReturns: MonthlyReturn[]
}

function fmt(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number(value).toFixed(digits)
}

function epochMs(ts: string | number): number | null {
  if (typeof ts === 'number') {
    return ts > 1e12 ? ts : ts * 1000
  }
  const parsed = Date.parse(String(ts))
  return Number.isNaN(parsed) ? null : parsed
}

export function computeSignalStats(
  trades: Trade[],
  durationDays: number | null,
): SignalStats {
  const buys = trades.filter((t) => t.side === 'buy')
  const sells = trades.filter((t) => t.side === 'sell')

  const buyCount = buys.length
  const sellCount = sells.length
  const buySellRatio = sellCount > 0 ? fmt(buyCount / sellCount, 2) : buyCount > 0 ? '∞' : '--'

  const buysWithPnl = buys.filter((t) => t.pnl !== undefined && t.pnl !== null)
  const sellsWithPnl = sells.filter((t) => t.pnl !== undefined && t.pnl !== null)

  const buyWins = buysWithPnl.filter((t) => (t.pnl as number) > 0).length
  const sellWins = sellsWithPnl.filter((t) => (t.pnl as number) > 0).length

  const buyWinRate = buysWithPnl.length > 0 ? fmt((buyWins / buysWithPnl.length) * 100, 1) + '%' : '--'
  const sellWinRate = sellsWithPnl.length > 0 ? fmt((sellWins / sellsWithPnl.length) * 100, 1) + '%' : '--'

  const avgBuyPnl = buysWithPnl.length > 0
    ? fmt(buysWithPnl.reduce((s, t) => s + (t.pnl as number), 0) / buysWithPnl.length, 4)
    : '--'
  const avgSellPnl = sellsWithPnl.length > 0
    ? fmt(sellsWithPnl.reduce((s, t) => s + (t.pnl as number), 0) / sellsWithPnl.length, 4)
    : '--'

  const tradesWithPnl = trades
    .map((t, i) => ({ pnl: t.pnl, index: i }))
    .filter((t) => t.pnl !== undefined && t.pnl !== null) as { pnl: number; index: number }[]

  let bestTrade: { pnl: number; index: number } | null = null
  let worstTrade: { pnl: number; index: number } | null = null

  for (const t of tradesWithPnl) {
    if (!bestTrade || t.pnl > bestTrade.pnl) bestTrade = t
    if (!worstTrade || t.pnl < worstTrade.pnl) worstTrade = t
  }

  const days = durationDays ?? 1
  const total = trades.length
  const signalFrequencyDaily = fmt(total / days, 2)
  const signalFrequencyWeekly = fmt(total / (days / 7), 2)

  const holdingDurations = computeTradeHoldingDurations(trades)
  const durations = [...holdingDurations.values()]
  const avgHoldingPeriod = durations.length > 0
    ? fmt(durations.reduce((a, b) => a + b, 0) / durations.length, 1)
    : '--'

  return {
    buyCount,
    sellCount,
    buySellRatio,
    buyWinRate,
    sellWinRate,
    avgBuyPnl,
    avgSellPnl,
    bestTrade,
    worstTrade,
    signalFrequencyDaily,
    signalFrequencyWeekly,
    avgHoldingPeriod,
  }
}

export function computeBenchmarkComparison(
  equityCurve: BacktestReportPoint[],
): BenchmarkComparison {
  if (equityCurve.length < 2) {
    return {
      benchmarkTotalReturn: null,
      excessReturn: null,
      trackingError: null,
      informationRatio: null,
    }
  }

  const first = equityCurve[0]
  const last = equityCurve[equityCurve.length - 1]

  const startBe = first.benchmark_equity
  const endBe = last.benchmark_equity
  const startEq = first.equity
  const endEq = last.equity

  if (!startBe || !startEq) {
    return {
      benchmarkTotalReturn: null,
      excessReturn: null,
      trackingError: null,
      informationRatio: null,
    }
  }

  const benchmarkTotalReturn = ((endBe - startBe) / startBe) * 100
  const strategyReturn = ((endEq - startEq) / startEq) * 100
  const excessReturn = strategyReturn - benchmarkTotalReturn

  const periodExcessReturns: number[] = []
  for (let i = 1; i < equityCurve.length; i++) {
    const prev = equityCurve[i - 1]
    const curr = equityCurve[i]
    if (prev.equity > 0 && prev.benchmark_equity > 0) {
      const stratRet = (curr.equity - prev.equity) / prev.equity
      const benchRet = (curr.benchmark_equity - prev.benchmark_equity) / prev.benchmark_equity
      periodExcessReturns.push(stratRet - benchRet)
    }
  }

  const mean = periodExcessReturns.length > 0
    ? periodExcessReturns.reduce((a, b) => a + b, 0) / periodExcessReturns.length
    : 0
  const variance = periodExcessReturns.length > 1
    ? periodExcessReturns.reduce((s, r) => s + (r - mean) ** 2, 0) / (periodExcessReturns.length - 1)
    : 0
  const trackingError = Math.sqrt(variance) * 100
  const informationRatio = trackingError > 0 ? excessReturn / trackingError : null

  return {
    benchmarkTotalReturn,
    excessReturn,
    trackingError,
    informationRatio,
  }
}

export function computeRiskMetrics(trades: Trade[]): RiskMetrics {
  const tradesWithPnl = trades
    .map((t) => t.pnl)
    .filter((p): p is number => p !== undefined && p !== null)

  if (tradesWithPnl.length === 0) {
    return {
      profitFactor: '--',
      expectancy: '--',
      maxConsecutiveWins: 0,
      valueAtRisk95: '--',
      avgWinningTrade: '--',
      avgLosingTrade: '--',
      varDisclaimer: false,
    }
  }

  const grossProfit = tradesWithPnl.filter((p) => p > 0).reduce((a, b) => a + b, 0)
  const grossLoss = Math.abs(tradesWithPnl.filter((p) => p < 0).reduce((a, b) => a + b, 0))
  const profitFactor = grossLoss > 0 ? fmt(grossProfit / grossLoss, 2) : grossProfit > 0 ? '∞' : '0'

  const expectancy = fmt(tradesWithPnl.reduce((a, b) => a + b, 0) / tradesWithPnl.length, 4)

  let maxConsecutiveWins = 0
  let currentStreak = 0
  for (const pnl of tradesWithPnl) {
    if (pnl > 0) {
      currentStreak += 1
      if (currentStreak > maxConsecutiveWins) maxConsecutiveWins = currentStreak
    } else {
      currentStreak = 0
    }
  }

  const sorted = [...tradesWithPnl].sort((a, b) => a - b)
  const varIndex = Math.floor(sorted.length * 0.05)
  const valueAtRisk95 = fmt(sorted[varIndex] ?? sorted[0], 4)

  const wins = tradesWithPnl.filter((p) => p > 0)
  const losses = tradesWithPnl.filter((p) => p < 0)
  const avgWinningTrade = wins.length > 0 ? fmt(wins.reduce((a, b) => a + b, 0) / wins.length, 4) : '--'
  const avgLosingTrade = losses.length > 0 ? fmt(losses.reduce((a, b) => a + b, 0) / losses.length, 4) : '--'

  return {
    profitFactor,
    expectancy,
    maxConsecutiveWins,
    valueAtRisk95,
    avgWinningTrade,
    avgLosingTrade,
    varDisclaimer: tradesWithPnl.length < 30,
  }
}

export function computeTradeDistribution(
  trades: Trade[],
  equityCurve: BacktestReportPoint[],
): TradeDistribution {
  const pnls = trades
    .map((t) => t.pnl)
    .filter((p): p is number => p !== undefined && p !== null)

  const pnlHistogramBuckets = buildPnlHistogram(pnls)
  const holdingDurationBuckets = buildDurationHistogram(trades)
  const monthlyReturns = buildMonthlyReturns(equityCurve)

  return { pnlHistogramBuckets, holdingDurationBuckets, monthlyReturns }
}

function buildPnlHistogram(pnls: number[]): PnlBucket[] {
  if (pnls.length === 0) return []

  const min = Math.min(...pnls)
  const max = Math.max(...pnls)
  const range = max - min

  if (range === 0) {
    return [{ range: fmt(min, 4), count: pnls.length }]
  }

  const bucketCount = Math.min(12, Math.max(4, Math.ceil(Math.sqrt(pnls.length))))
  const step = range / bucketCount
  const buckets: PnlBucket[] = []

  for (let i = 0; i < bucketCount; i++) {
    const lo = min + i * step
    const hi = lo + step
    const count = pnls.filter((p) => i === bucketCount - 1 ? (p >= lo && p <= hi) : (p >= lo && p < hi)).length
    buckets.push({ range: `${fmt(lo, 2)} ~ ${fmt(hi, 2)}`, count })
  }

  return buckets
}

function buildDurationHistogram(trades: Trade[]): DurationBucket[] {
  const durations = computeTradeHoldingDurations(trades)
  const values = [...durations.values()]

  if (values.length === 0) return []

  const ranges = [
    { label: '0-1d', lo: 0, hi: 1 },
    { label: '1-3d', lo: 1, hi: 3 },
    { label: '3-7d', lo: 3, hi: 7 },
    { label: '7-14d', lo: 7, hi: 14 },
    { label: '14-30d', lo: 14, hi: 30 },
    { label: '30d+', lo: 30, hi: Infinity },
  ]

  return ranges
    .map(({ label, lo, hi }) => ({
      range: label,
      count: values.filter((d) => hi === Infinity ? d >= lo : (d >= lo && d < hi)).length,
    }))
    .filter((b) => b.count > 0)
}

function buildMonthlyReturns(equityCurve: BacktestReportPoint[]): MonthlyReturn[] {
  if (equityCurve.length < 2) return []

  const monthMap = new Map<string, { first: BacktestReportPoint; last: BacktestReportPoint }>()

  for (const point of equityCurve) {
    const d = new Date(point.timestamp)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const existing = monthMap.get(key)
    if (!existing) {
      monthMap.set(key, { first: point, last: point })
    } else {
      existing.last = point
    }
  }

  const result: MonthlyReturn[] = []
  for (const [month, { first, last }] of monthMap) {
    if (first.equity > 0) {
      const returnPct = ((last.equity - first.equity) / first.equity) * 100
      result.push({ month, returnPct })
    } else {
      result.push({ month, returnPct: null })
    }
  }

  return result
}

export function computeTradeHoldingDurations(trades: Trade[]): Map<number, number> {
  const result = new Map<number, number>()
  const buyQueue: { index: number; timestampMs: number }[] = []

  const sorted = trades
    .map((t, i) => ({ ...t, originalIndex: i }))
    .sort((a, b) => {
      const aMs = epochMs(a.timestamp) ?? 0
      const bMs = epochMs(b.timestamp) ?? 0
      return aMs - bMs
    })

  for (const trade of sorted) {
    const tsMs = epochMs(trade.timestamp)
    if (tsMs === null) continue

    if (trade.side === 'buy') {
      buyQueue.push({ index: trade.originalIndex, timestampMs: tsMs })
    } else if (trade.side === 'sell' && buyQueue.length > 0) {
      const matched = buyQueue.shift()!
      const days = (tsMs - matched.timestampMs) / 86400000
      result.set(matched.index, Math.round(days * 10) / 10)
      result.set(trade.originalIndex, Math.round(days * 10) / 10)
    }
  }

  return result
}

export function computeCumulativeReturns(trades: Trade[]): number[] {
  const cumSum: number[] = []
  let running = 0

  for (const trade of trades) {
    if (trade.pnl !== undefined && trade.pnl !== null) {
      running += trade.pnl
    }
    cumSum.push(running)
  }

  return cumSum
}
