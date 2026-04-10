import type { KlineBar } from '../types/KlineBar'
import type { Trade } from '../types/Trade'

export interface TradeMarker {
  id: string
  symbol: string
  side: Trade['side']
  price: number
  quantity: number
  pnl?: number
  timestamp: string | number
  epochMs: number
  barIndex: number
  barTime: string | number
}

export interface EnrichedKlineBar extends KlineBar {
  signals?: TradeMarker[]
}

export function toEpochMs(value: string | number): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    if (value > 1e12) return value
    if (value > 1e9) return value * 1000
    return null
  }

  const trimmed = value.trim()
  if (!trimmed) return null

  if (/^\d+$/.test(trimmed)) {
    const parsed = Number(trimmed)
    if (parsed > 1e12) return parsed
    if (parsed > 1e9) return parsed * 1000
    return null
  }

  const iso = Date.parse(trimmed)
  return Number.isNaN(iso) ? null : iso
}

export function simpleMovingAverage(values: number[], period: number): Array<number | null> {
  if (period <= 0) {
    return values.map(() => null)
  }

  const result: Array<number | null> = []
  let runningSum = 0

  values.forEach((value, index) => {
    runningSum += value
    if (index >= period) {
      runningSum -= values[index - period]
    }

    if (index + 1 < period) {
      result.push(null)
      return
    }

    result.push(Number((runningSum / period).toFixed(6)))
  })

  return result
}

function findTradeBarIndex(barTimes: Array<number | null>, tradeTime: number): number {
  let targetIndex = barTimes.findIndex((barTime) => barTime === tradeTime)
  if (targetIndex !== -1) {
    return targetIndex
  }

  targetIndex = barTimes.reduce((latestIndex, barTime, index) => {
    if (barTime === null || barTime > tradeTime) return latestIndex
    return barTime >= (barTimes[latestIndex] ?? -Infinity) ? index : latestIndex
  }, -1)

  return targetIndex
}

export function mapTradesToMarkers(bars: KlineBar[], trades: Trade[]): TradeMarker[] {
  if (!bars.length || !trades.length) return []

  const barTimes = bars.map((bar) => toEpochMs(bar.time))

  return trades.flatMap((trade, index) => {
    const tradeTime = toEpochMs(trade.timestamp)
    if (tradeTime === null) {
      return []
    }

    const barIndex = findTradeBarIndex(barTimes, tradeTime)
    if (barIndex < 0) {
      return []
    }

    const bar = bars[barIndex]
    if (!bar) {
      return []
    }

    return [{
      id: trade.id ?? `${trade.side}-${tradeTime}-${index}`,
      symbol: trade.symbol,
      side: trade.side,
      price: trade.price,
      quantity: trade.quantity,
      pnl: trade.pnl,
      timestamp: trade.timestamp,
      epochMs: tradeTime,
      barIndex,
      barTime: bar.time,
    }]
  })
}

export function mapTradeSignalsToBars(bars: KlineBar[], trades: Trade[]): EnrichedKlineBar[] {
  if (!bars.length) return []
  if (!trades.length) return bars.map((bar) => ({ ...bar }))

  const withSignal = bars.map((bar) => ({ ...bar })) as EnrichedKlineBar[]
  const markers = mapTradesToMarkers(bars, trades)

  for (const marker of markers) {
    const targetBar = withSignal[marker.barIndex]
    if (targetBar) {
      targetBar.signals = [...(targetBar.signals ?? []), marker]
      targetBar.signal = marker.side
    }
  }

  return withSignal
}
