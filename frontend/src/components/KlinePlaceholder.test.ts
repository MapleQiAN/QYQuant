// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'
import KlinePlaceholder from './KlinePlaceholder.vue'

const { initMock, setOptionMock, resizeMock, disposeMock } = vi.hoisted(() => ({
  setOptionMock: vi.fn(),
  resizeMock: vi.fn(),
  disposeMock: vi.fn(),
  initMock: vi.fn(),
}))

vi.mock('echarts', () => ({
  init: initMock,
}))

class ResizeObserverMock {
  observe = vi.fn()
  disconnect = vi.fn()
}

function buildI18n() {
  return createI18n({
    legacy: false,
    locale: 'zh',
    messages: {
      zh: {
        kline: {
          candles: 'K线',
          volume: '成交量',
          buySignal: '买入信号',
          sellSignal: '卖出信号',
          noData: '暂无数据',
          timeframes: {
            '1m': '1分钟',
            '5m': '5分钟',
            '15m': '15分钟',
            '1h': '1小时',
            '4h': '4小时',
            '1d': '日线',
          },
        },
      },
    },
    missingWarn: false,
    fallbackWarn: false,
  })
}

describe('KlinePlaceholder', () => {
  beforeEach(() => {
    setOptionMock.mockClear()
    resizeMock.mockClear()
    disposeMock.mockClear()
    initMock.mockClear()
    initMock.mockReturnValue({
      setOption: setOptionMock,
      resize: resizeMock,
      dispose: disposeMock,
    })
    vi.stubGlobal('ResizeObserver', ResizeObserverMock)
  })

  it('anchors trade markers to candle extremes instead of outlier fill prices', async () => {
    mount(KlinePlaceholder, {
      props: {
        symbol: 'BTCUSDT',
        timeframe: '1d',
        data: [
          { time: 1700000000000, open: 100, high: 110, low: 95, close: 108, volume: 1000 },
          { time: 1700086400000, open: 108, high: 112, low: 104, close: 106, volume: 1200 },
        ],
        trades: [
          { id: 'buy-1', symbol: 'BTCUSDT', side: 'buy', price: 880, quantity: 1, timestamp: 1700000000000 },
          { id: 'sell-1', symbol: 'BTCUSDT', side: 'sell', price: 1180, quantity: 1, timestamp: 1700086400000 },
        ],
      },
      global: {
        plugins: [buildI18n()],
      },
    })

    await nextTick()

    const option = setOptionMock.mock.calls[setOptionMock.mock.calls.length - 1]?.[0]
    const buySeries = option?.series?.find((series: any) => series.name === '买入信号')
    const sellSeries = option?.series?.find((series: any) => series.name === '卖出信号')

    expect(buySeries?.data?.[0]?.value).toEqual([1700000000000, 95])
    expect(sellSeries?.data?.[0]?.value).toEqual([1700086400000, 112])
    expect(buySeries?.data?.[0]?.marker?.price).toBe(880)
    expect(sellSeries?.data?.[0]?.marker?.price).toBe(1180)
  })
})
