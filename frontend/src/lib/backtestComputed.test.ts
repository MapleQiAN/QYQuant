import { describe, it, expect } from 'vitest'
import type { Trade } from '../types/Trade'
import type { BacktestReportPoint } from '../types/Backtest'
import {
  computeSignalStats,
  computeBenchmarkComparison,
  computeRiskMetrics,
  computeTradeDistribution,
  computeTradeHoldingDurations,
  computeCumulativeReturns,
} from './backtestComputed'

function makeTrade(overrides: Partial<Trade> & { side: 'buy' | 'sell' }): Trade {
  return {
    symbol: 'BTCUSDT',
    price: 100,
    quantity: 1,
    timestamp: Date.now(),
    ...overrides,
  }
}

function makePoint(overrides: Partial<BacktestReportPoint>): BacktestReportPoint {
  return {
    timestamp: Date.now(),
    equity: 10000,
    benchmark_equity: 10000,
    ...overrides,
  }
}

describe('computeSignalStats', () => {
  it('returns defaults for empty trades', () => {
    const stats = computeSignalStats([], null)
    expect(stats.buyCount).toBe(0)
    expect(stats.sellCount).toBe(0)
    expect(stats.buySellRatio).toBe('--')
    expect(stats.bestTrade).toBeNull()
    expect(stats.worstTrade).toBeNull()
  })

  it('counts buy and sell signals', () => {
    const trades = [
      makeTrade({ side: 'buy' }),
      makeTrade({ side: 'buy' }),
      makeTrade({ side: 'sell' }),
    ]
    const stats = computeSignalStats(trades, 10)
    expect(stats.buyCount).toBe(2)
    expect(stats.sellCount).toBe(1)
    expect(stats.buySellRatio).toBe('2.00')
  })

  it('computes win rates', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 10 }),
      makeTrade({ side: 'buy', pnl: -5 }),
      makeTrade({ side: 'sell', pnl: 20 }),
    ]
    const stats = computeSignalStats(trades, 10)
    expect(stats.buyWinRate).toBe('50.0%')
    expect(stats.sellWinRate).toBe('100.0%')
  })

  it('finds best and worst trades', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: -20 }),
      makeTrade({ side: 'buy', pnl: 50 }),
      makeTrade({ side: 'sell', pnl: 10 }),
    ]
    const stats = computeSignalStats(trades, 10)
    expect(stats.bestTrade?.pnl).toBe(50)
    expect(stats.worstTrade?.pnl).toBe(-20)
  })

  it('computes signal frequency', () => {
    const trades = Array.from({ length: 14 }, (_, i) =>
      makeTrade({ side: i % 2 === 0 ? 'buy' as const : 'sell' as const }),
    )
    const stats = computeSignalStats(trades, 7)
    expect(stats.signalFrequencyDaily).toBe('2.00')
    expect(stats.signalFrequencyWeekly).toBe('14.00')
  })
})

describe('computeBenchmarkComparison', () => {
  it('returns nulls for empty curve', () => {
    const result = computeBenchmarkComparison([])
    expect(result.benchmarkTotalReturn).toBeNull()
    expect(result.excessReturn).toBeNull()
  })

  it('returns nulls for single point', () => {
    const result = computeBenchmarkComparison([makePoint({})])
    expect(result.benchmarkTotalReturn).toBeNull()
  })

  it('computes benchmark return and excess return', () => {
    const points = [
      makePoint({ equity: 10000, benchmark_equity: 10000 }),
      makePoint({ equity: 11000, benchmark_equity: 10500 }),
    ]
    const result = computeBenchmarkComparison(points)
    expect(result.benchmarkTotalReturn).toBeCloseTo(5, 1)
    expect(result.excessReturn).toBeCloseTo(5, 1)
  })

  it('computes tracking error and information ratio', () => {
    const points = [
      makePoint({ equity: 10000, benchmark_equity: 10000 }),
      makePoint({ equity: 10100, benchmark_equity: 10050 }),
      makePoint({ equity: 10200, benchmark_equity: 10100 }),
    ]
    const result = computeBenchmarkComparison(points)
    expect(result.trackingError).not.toBeNull()
    expect(result.informationRatio).not.toBeNull()
  })
})

describe('computeRiskMetrics', () => {
  it('returns defaults for empty trades', () => {
    const metrics = computeRiskMetrics([])
    expect(metrics.profitFactor).toBe('--')
    expect(metrics.expectancy).toBe('--')
    expect(metrics.maxConsecutiveWins).toBe(0)
  })

  it('computes profit factor', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 100 }),
      makeTrade({ side: 'sell', pnl: -40 }),
      makeTrade({ side: 'buy', pnl: 60 }),
    ]
    const metrics = computeRiskMetrics(trades)
    expect(metrics.profitFactor).toBe('4.00')
  })

  it('computes expectancy', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 30 }),
      makeTrade({ side: 'sell', pnl: -10 }),
    ]
    const metrics = computeRiskMetrics(trades)
    expect(metrics.expectancy).toBe('10.0000')
  })

  it('computes max consecutive wins', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 10 }),
      makeTrade({ side: 'buy', pnl: 20 }),
      makeTrade({ side: 'sell', pnl: -5 }),
      makeTrade({ side: 'buy', pnl: 30 }),
      makeTrade({ side: 'buy', pnl: 40 }),
      makeTrade({ side: 'buy', pnl: 50 }),
    ]
    const metrics = computeRiskMetrics(trades)
    expect(metrics.maxConsecutiveWins).toBe(3)
  })

  it('shows var disclaimer when < 30 trades', () => {
    const trades = Array.from({ length: 10 }, () =>
      makeTrade({ side: 'buy', pnl: Math.random() * 10 }),
    )
    const metrics = computeRiskMetrics(trades)
    expect(metrics.varDisclaimer).toBe(true)
  })

  it('hides var disclaimer when >= 30 trades', () => {
    const trades = Array.from({ length: 30 }, () =>
      makeTrade({ side: 'buy', pnl: Math.random() * 10 }),
    )
    const metrics = computeRiskMetrics(trades)
    expect(metrics.varDisclaimer).toBe(false)
  })

  it('computes avg winning and losing trades', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 100 }),
      makeTrade({ side: 'sell', pnl: -50 }),
      makeTrade({ side: 'buy', pnl: 200 }),
      makeTrade({ side: 'sell', pnl: -30 }),
    ]
    const metrics = computeRiskMetrics(trades)
    expect(metrics.avgWinningTrade).toBe('150.0000')
    expect(metrics.avgLosingTrade).toBe('-40.0000')
  })
})

describe('computeTradeHoldingDurations', () => {
  it('returns empty map for no trades', () => {
    const result = computeTradeHoldingDurations([])
    expect(result.size).toBe(0)
  })

  it('pairs buy→sell via FIFO', () => {
    const baseTs = 1700000000000
    const trades = [
      makeTrade({ side: 'buy', timestamp: baseTs }),
      makeTrade({ side: 'sell', timestamp: baseTs + 86400000 * 3 }),
    ]
    const durations = computeTradeHoldingDurations(trades)
    expect(durations.size).toBe(2)
    expect(durations.get(0)).toBe(3)
    expect(durations.get(1)).toBe(3)
  })

  it('handles unpaired trades', () => {
    const trades = [
      makeTrade({ side: 'buy', timestamp: Date.now() }),
    ]
    const durations = computeTradeHoldingDurations(trades)
    expect(durations.size).toBe(0)
  })
})

describe('computeCumulativeReturns', () => {
  it('returns empty array for no trades', () => {
    expect(computeCumulativeReturns([])).toEqual([])
  })

  it('computes running sum', () => {
    const trades = [
      makeTrade({ side: 'buy', pnl: 10 }),
      makeTrade({ side: 'sell', pnl: -3 }),
      makeTrade({ side: 'buy', pnl: 7 }),
    ]
    const result = computeCumulativeReturns(trades)
    expect(result).toEqual([10, 7, 14])
  })

  it('treats undefined pnl as 0', () => {
    const trades = [
      makeTrade({ side: 'buy' }),
      makeTrade({ side: 'sell', pnl: 5 }),
    ]
    const result = computeCumulativeReturns(trades)
    expect(result).toEqual([0, 5])
  })
})

describe('computeTradeDistribution', () => {
  it('returns empty arrays for no trades', () => {
    const result = computeTradeDistribution([], [])
    expect(result.pnlHistogramBuckets).toEqual([])
    expect(result.holdingDurationBuckets).toEqual([])
    expect(result.monthlyReturns).toEqual([])
  })

  it('builds pnl histogram', () => {
    const trades = Array.from({ length: 20 }, (_, i) =>
      makeTrade({ side: 'buy', pnl: (i - 10) * 5 }),
    )
    const result = computeTradeDistribution(trades, [])
    expect(result.pnlHistogramBuckets.length).toBeGreaterThan(0)
    const totalCount = result.pnlHistogramBuckets.reduce((s, b) => s + b.count, 0)
    expect(totalCount).toBe(20)
  })

  it('builds monthly returns', () => {
    const points = [
      makePoint({ timestamp: new Date('2024-01-01T00:00:00Z').getTime(), equity: 10000 }),
      makePoint({ timestamp: new Date('2024-01-15T00:00:00Z').getTime(), equity: 10500 }),
      makePoint({ timestamp: new Date('2024-02-01T00:00:00Z').getTime(), equity: 10200 }),
    ]
    const result = computeTradeDistribution([], points)
    expect(result.monthlyReturns.length).toBe(2)
    expect(result.monthlyReturns[0]?.returnPct).toBeCloseTo(5, 1)
  })
})
