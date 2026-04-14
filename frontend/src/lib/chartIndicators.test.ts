import { describe, expect, it } from 'vitest'
import type { KlineBar } from '../types/KlineBar'
import type { Trade } from '../types/Trade'
import {
  buildPositionedTradeMarkers,
  mapTradeSignalsToBars,
  mapTradesToMarkers,
  simpleMovingAverage,
} from './chartIndicators'

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

    const mapped = mapTradeSignalsToBars(bars, trades)

    expect(mapped.map((bar) => bar.signal)).toEqual(['buy', undefined, 'sell'])
    expect(mapped[0]?.signals?.map((signal) => signal.price)).toEqual([10.2])
    expect(mapped[2]?.signals?.map((signal) => signal.price)).toEqual([12.1])
  })

  it('keeps multiple trade markers on the same bar and preserves exact trade prices', () => {
    const bars: KlineBar[] = [
      { time: 1700000000000, open: 10, high: 11, low: 9, close: 10, volume: 100 },
      { time: 1700000060000, open: 10, high: 12, low: 10, close: 11, volume: 130 },
      { time: 1700000120000, open: 11, high: 13, low: 10, close: 12, volume: 120 }
    ]
    const trades: Trade[] = [
      { id: 'buy-1', symbol: 'XAUUSD', side: 'buy', price: 10.55, quantity: 1, timestamp: '2023-11-14T22:14:10.000Z' },
      { id: 'sell-1', symbol: 'XAUUSD', side: 'sell', price: 10.95, quantity: 1, timestamp: '2023-11-14T22:14:45.000Z', pnl: 4.2 }
    ]

    const markers = mapTradesToMarkers(bars, trades)
    const enrichedBars = mapTradeSignalsToBars(bars, trades)

    expect(markers).toEqual([
      expect.objectContaining({ id: 'buy-1', barIndex: 0, price: 10.55, side: 'buy' }),
      expect.objectContaining({ id: 'sell-1', barIndex: 0, price: 10.95, side: 'sell', pnl: 4.2 }),
    ])
    expect(enrichedBars[0]?.signals?.map((signal) => signal.id)).toEqual(['buy-1', 'sell-1'])
    expect(enrichedBars[0]?.signals?.map((signal) => signal.price)).toEqual([10.55, 10.95])
    expect(enrichedBars[0]?.signal).toBe('sell')
  })

  it('keeps trade markers anchored to fill price and stacks them with pixel offsets', () => {
    const bars: KlineBar[] = [
      { time: 1700000000000, open: 10, high: 12, low: 9, close: 11, volume: 100 },
      { time: 1700000060000, open: 11, high: 13, low: 10, close: 12, volume: 130 },
    ]
    const trades: Trade[] = [
      { id: 'buy-1', symbol: 'XAUUSD', side: 'buy', price: 9.3, quantity: 1, timestamp: 1700000000000 },
      { id: 'buy-2', symbol: 'XAUUSD', side: 'buy', price: 9.1, quantity: 1, timestamp: 1700000010000 },
      { id: 'sell-1', symbol: 'XAUUSD', side: 'sell', price: 12.2, quantity: 1, timestamp: 1700000015000 },
      { id: 'sell-2', symbol: 'XAUUSD', side: 'sell', price: 12.4, quantity: 1, timestamp: 1700000020000 },
    ]

    const markers = buildPositionedTradeMarkers(bars, trades)
    const buyMarkers = markers.filter((marker) => marker.side === 'buy')
    const sellMarkers = markers.filter((marker) => marker.side === 'sell')

    expect(markers).toHaveLength(4)
    expect(buyMarkers[0]).toEqual(expect.objectContaining({ id: 'buy-1', stackIndex: 0 }))
    expect(buyMarkers[1]).toEqual(expect.objectContaining({ id: 'buy-2', stackIndex: 1 }))
    expect(sellMarkers[0]).toEqual(expect.objectContaining({ id: 'sell-1', stackIndex: 0 }))
    expect(sellMarkers[1]).toEqual(expect.objectContaining({ id: 'sell-2', stackIndex: 1 }))
    expect(buyMarkers[0]?.price).toBe(9.3)
    expect(buyMarkers[1]?.price).toBe(9.1)
    expect(sellMarkers[0]?.price).toBe(12.2)
    expect(sellMarkers[1]?.price).toBe(12.4)
    expect(buyMarkers[0]?.symbolOffset).toEqual([0, 18])
    expect(buyMarkers[1]?.symbolOffset).toEqual([0, 32])
    expect(sellMarkers[0]?.symbolOffset).toEqual([0, -18])
    expect(sellMarkers[1]?.symbolOffset).toEqual([0, -32])
  })
})
