// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import BacktestCard from './BacktestCard.vue'

const { downloadJsonMock } = vi.hoisted(() => ({
  downloadJsonMock: vi.fn()
}))

vi.mock('../lib/download', () => ({
  downloadJson: downloadJsonMock
}))

describe('BacktestCard', () => {
  beforeEach(() => {
    downloadJsonMock.mockReset()
  })

  it('exports the current snapshot when export is clicked', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: { en: {} },
      missingWarn: false,
      fallbackWarn: false
    })

    const wrapper = mount(BacktestCard, {
      props: {
        data: {
          summary: {
            totalReturn: 12,
            annualizedReturn: 10,
            sharpeRatio: 1.4,
            maxDrawdown: -4,
            winRate: 56,
            profitFactor: 1.8,
            totalTrades: 18,
            avgHoldingDays: 3
          },
          kline: [],
          trades: [],
          dataSource: 'mock'
        }
      },
      global: {
        plugins: [i18n],
        stubs: {
          KlinePlaceholder: true,
          StatCard: {
            template: '<div />'
          },
          EmptyState: true,
          ErrorState: true,
          SkeletonState: true
        }
      }
    })

    await wrapper.get('[data-test="backtest-export"]').trigger('click')

    expect(downloadJsonMock).toHaveBeenCalledTimes(1)
    expect(downloadJsonMock.mock.calls[0]?.[0]).toContain('backtest')
    expect(downloadJsonMock.mock.calls[0]?.[1]).toMatchObject({
      summary: expect.objectContaining({ totalReturn: 12 }),
      dataSource: 'mock'
    })
  })

  it('renders joinquant and akshare as selectable data sources', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: {
        en: {
          backtest: {
            title: 'Backtest',
            statusCompleted: 'Completed',
            dataSource: 'Data source',
            dataSourceAuto: 'Auto',
            dataSourceBinance: 'Binance',
            dataSourceFreegold: 'FreeGold',
            dataSourceJoinquant: 'JoinQuant',
            dataSourceAkshare: 'AkShare',
            dataSourceMock: 'Mock',
            dataSourceAutoWith: 'Auto · {source}',
            refresh: 'Refresh',
            export: 'Export'
          },
          common: {
            retry: 'Retry'
          }
        }
      },
      missingWarn: false,
      fallbackWarn: false
    })

    const wrapper = mount(BacktestCard, {
      props: {
        data: {
          summary: {
            totalReturn: 12,
            annualizedReturn: 10,
            sharpeRatio: 1.4,
            maxDrawdown: -4,
            winRate: 56,
            profitFactor: 1.8,
            totalTrades: 18,
            avgHoldingDays: 3
          },
          kline: [],
          trades: [],
          dataSource: 'joinquant'
        }
      },
      global: {
        plugins: [i18n],
        stubs: {
          KlinePlaceholder: true,
          StatCard: {
            template: '<div />'
          },
          EmptyState: true,
          ErrorState: true,
          SkeletonState: true
        }
      }
    })

    const optionValues = wrapper.findAll('option').map((option) => option.attributes('value'))

    expect(optionValues).toEqual(['auto', 'joinquant', 'akshare', 'binance', 'freegold', 'mock'])
  })
})
