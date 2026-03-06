import type { KlineBar } from '../types/KlineBar'
import type { Trade } from '../types/Trade'

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

export function mapTradeSignalsToBars(bars: KlineBar[], trades: Trade[]): KlineBar[] {
  if (!bars.length || !trades.length) return bars

  const withSignal = bars.map((bar) => ({ ...bar }))
  const barTimes = bars.map((bar) => toEpochMs(bar.time))

  for (const trade of trades) {
    const tradeTime = toEpochMs(trade.timestamp)
    if (tradeTime === null) continue

    let targetIndex = barTimes.findIndex((barTime) => barTime === tradeTime)
    if (targetIndex === -1) {
      targetIndex = barTimes.reduce((latestIndex, barTime, index) => {
        if (barTime === null || barTime > tradeTime) return latestIndex
        return barTime >= (barTimes[latestIndex] ?? -Infinity) ? index : latestIndex
      }, -1)
    }

    if (targetIndex >= 0) {
      withSignal[targetIndex].signal = trade.side
    }
  }

  return withSignal
}
