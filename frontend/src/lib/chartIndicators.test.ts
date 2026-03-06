import { describe, expect, it } from 'vitest'
import type { KlineBar } from '../types/KlineBar'
import type { Trade } from '../types/Trade'
import { mapTradeSignalsToBars, simpleMovingAverage } from './chartIndicators'

describe('chartIndicators', () => {
  it('calculates SMA with null warm-up values', () => {
    const values = [1, 2, 3, 4, 5]
    expect(simpleMovingAverage(values, 3)).toEqual([null, null, 2, 3, 4])
  })

  it('maps trades to buy/sell signals on bars by timestamp', () => {
    const bars: KlineBar[] = [
      { time: 1700000000000, open: 10, high: 11, low: 9, close: 10, volume: 100 },
      { time: 1700000060000, open: 10, high: 12, low: 10, close: 11, volume: 130 },
      { time: 1700000120000, open: 11, high: 13, low: 10, close: 12, volume: 120 }
    ]
    const trades: Trade[] = [
      { id: 't1', symbol: 'XAUUSD', side: 'buy', price: 10.2, quantity: 1, timestamp: '2023-11-14T22:13:20.000Z' },
      { id: 't2', symbol: 'XAUUSD', side: 'sell', price: 12.1, quantity: 1, timestamp: '2023-11-14T22:15:20.000Z' }
    ]

    expect(mapTradeSignalsToBars(bars, trades).map((bar) => bar.signal)).toEqual(['buy', undefined, 'sell'])
  })
})
