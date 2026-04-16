// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyDetailView from './StrategyDetailView.vue'

const {
  fetchStrategyParametersMock,
  fetchBacktestStatusMock,
  submitBacktestMock,
  loadPresetsMock,
  savePresetMock,
  removePresetMock,
} = vi.hoisted(() => ({
  fetchStrategyParametersMock: vi.fn(),
  fetchBacktestStatusMock: vi.fn(),
  submitBacktestMock: vi.fn(),
  loadPresetsMock: vi.fn(),
  savePresetMock: vi.fn(),
  removePresetMock: vi.fn(),
}))

const presetsStoreState = {
  presets: [] as Array<any>,
  loading: false,
  error: null as string | null,
}

const routeState = vi.hoisted(() => ({
  params: {
    strategyId: 'strategy-1',
  },
  query: {} as Record<string, string>,
}))

vi.mock('vue-router', () => ({
  RouterLink: { template: '<a><slot /></a>' },
  useRouter: () => ({
    push: vi.fn(),
  }),
  useRoute: () => routeState,
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, string>) => (params?.jobId ? `${key}:${params.jobId}` : key),
  }),
}))

vi.mock('../api/strategies', () => ({
  fetchStrategyParameters: fetchStrategyParametersMock,
}))

vi.mock('../api/backtests', async () => {
  const actual = await vi.importActual<typeof import('../api/backtests')>('../api/backtests')
  return {
    ...actual,
    fetchBacktestStatus: fetchBacktestStatusMock,
    submitBacktest: submitBacktestMock,
  }
})

vi.mock('../stores', () => ({
  useUserStore: () => ({
    onboardingHighlightTarget: null,
    setGuidedBacktestJob: vi.fn(),
    setGuidedBacktestStep: vi.fn(),
    setOnboardingHighlightTarget: vi.fn(),
  }),
}))

vi.mock('../stores/usePresetsStore', () => ({
  usePresetsStore: () => ({
    ...presetsStoreState,
    loadPresets: loadPresetsMock,
    savePreset: savePresetMock,
    removePreset: removePresetMock,
  }),
}))

describe('StrategyDetailView', () => {
  beforeEach(() => {
    fetchStrategyParametersMock.mockReset()
    fetchBacktestStatusMock.mockReset()
    submitBacktestMock.mockReset()
    loadPresetsMock.mockReset()
    savePresetMock.mockReset()
    removePresetMock.mockReset()
    presetsStoreState.presets = []
    presetsStoreState.loading = false
    presetsStoreState.error = null
    routeState.params.strategyId = 'strategy-1'
    routeState.query = {}
  })

  it('loads parameter definitions and submits a backtest', async () => {
    fetchStrategyParametersMock.mockResolvedValue([
      {
        name: 'window',
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        step: 1,
        required: false,
      },
    ])
    submitBacktestMock.mockResolvedValue({ job_id: 'job-1' })

    const wrapper = mount(StrategyDetailView, {
      global: {
        mocks: {
          $t: (key: string, params?: Record<string, string>) => (params?.jobId ? `${key}:${params.jobId}` : key),
        },
      },
    })
    await flushPromises()

    expect(fetchStrategyParametersMock).toHaveBeenCalledWith('strategy-1')
    expect(loadPresetsMock).toHaveBeenCalledWith('strategy-1')

    await wrapper.get('[data-test="symbol-input"]').setValue('BTCUSDT')
    await wrapper.get('[data-test="start-date-input"]').setValue('2024-01-01')
    await wrapper.get('[data-test="end-date-input"]').setValue('2024-01-31')
    await wrapper.get('[data-test="data-source-select"]').setValue('binance')
    await wrapper.get('[data-test="start-backtest"]').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalledWith({
      strategy_id: 'strategy-1',
      symbols: ['BTCUSDT'],
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      data_source: 'binance',
      parameters: { window: 20 },
    })
    expect(wrapper.text()).toContain('strategyDetail.backtestSubmitted:job-1')
  })

  it('auto-resolves A-share symbol to akshare when data source stays auto', async () => {
    fetchStrategyParametersMock.mockResolvedValue([
      {
        name: 'window',
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        step: 1,
        required: false,
      },
    ])
    submitBacktestMock.mockResolvedValue({ job_id: 'job-2' })

    const wrapper = mount(StrategyDetailView)
    await flushPromises()

    await wrapper.get('[data-test="symbol-input"]').setValue('002028.XSHE')
    await wrapper.get('[data-test="start-date-input"]').setValue('2024-01-01')
    await wrapper.get('[data-test="end-date-input"]').setValue('2024-01-31')
    await wrapper.get('[data-test="start-backtest"]').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        data_source: 'akshare',
      })
    )
  })

  it('blocks incompatible data source for A-share symbols', async () => {
    fetchStrategyParametersMock.mockResolvedValue([
      {
        name: 'window',
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        step: 1,
        required: false,
      },
    ])

    const wrapper = mount(StrategyDetailView)
    await flushPromises()

    await wrapper.get('[data-test="symbol-input"]').setValue('002028.XSHE')
    await wrapper.get('[data-test="data-source-select"]').setValue('binance')
    await wrapper.get('[data-test="start-date-input"]').setValue('2024-01-01')
    await wrapper.get('[data-test="end-date-input"]').setValue('2024-01-31')
    await wrapper.get('[data-test="start-backtest"]').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('strategyDetail.errorIncompatibleDataSource')
  })

  it('shows detailed failure reason when guided polling sees a failed job', async () => {
    routeState.query = { guided: 'true' }
    fetchStrategyParametersMock.mockResolvedValue([
      {
        name: 'window',
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        step: 1,
        required: false,
      },
    ])
    submitBacktestMock.mockResolvedValue({ job_id: 'job-1' })
    fetchBacktestStatusMock.mockResolvedValue({
      status: 'failed',
      error: {
        type: 'NameError',
        line: 15,
        message: "Undefined variable 'sma_period'",
      },
    })

    const wrapper = mount(StrategyDetailView, {
      global: {
        mocks: {
          $t: (key: string, params?: Record<string, string>) => (params?.jobId ? `${key}:${params.jobId}` : key),
        },
      },
    })
    await flushPromises()

    await wrapper.get('[data-test="symbol-input"]').setValue('BTCUSDT')
    await wrapper.get('[data-test="start-date-input"]').setValue('2024-01-01')
    await wrapper.get('[data-test="end-date-input"]').setValue('2024-01-31')
    await wrapper.get('[data-test="start-backtest"]').trigger('click')
    await flushPromises()

    expect(fetchBacktestStatusMock).toHaveBeenCalledWith('job-1')
    expect(wrapper.text()).toContain("Backtest failed: Undefined variable 'sma_period' (line 15)")
  })

  it('shows next-step guidance when arriving from template creation', async () => {
    routeState.query = { guided: 'true', source: 'template' }
    fetchStrategyParametersMock.mockResolvedValue([
      {
        name: 'window',
        type: 'int',
        default: 20,
        min: 5,
        max: 50,
        step: 1,
        required: false,
      },
    ])

    const wrapper = mount(StrategyDetailView, {
      global: {
        mocks: {
          $t: (key: string, params?: Record<string, string>) => (params?.jobId ? `${key}:${params.jobId}` : key),
        },
      },
    })
    await flushPromises()

    expect(wrapper.get('[data-test="guided-next-steps"]').text()).toContain('strategyDetail.nextStepsTitle')
    expect(wrapper.text()).toContain('strategyDetail.nextStepsTemplate')
    expect(wrapper.text()).toContain('strategyDetail.nextStepsRun')
  })
})
