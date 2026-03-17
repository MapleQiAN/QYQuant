// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyDetailView from './StrategyDetailView.vue'

const {
  fetchStrategyParametersMock,
  submitBacktestMock,
  loadPresetsMock,
  savePresetMock,
  removePresetMock,
} = vi.hoisted(() => ({
  fetchStrategyParametersMock: vi.fn(),
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

vi.mock('vue-router', () => ({
  RouterLink: { template: '<a><slot /></a>' },
  useRoute: () => ({
    params: {
      strategyId: 'strategy-1',
    },
  }),
}))

vi.mock('../api/strategies', () => ({
  fetchStrategyParameters: fetchStrategyParametersMock,
}))

vi.mock('../api/backtests', () => ({
  submitBacktest: submitBacktestMock,
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
    submitBacktestMock.mockReset()
    loadPresetsMock.mockReset()
    savePresetMock.mockReset()
    removePresetMock.mockReset()
    presetsStoreState.presets = []
    presetsStoreState.loading = false
    presetsStoreState.error = null
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

    const wrapper = mount(StrategyDetailView)
    await flushPromises()

    expect(fetchStrategyParametersMock).toHaveBeenCalledWith('strategy-1')
    expect(loadPresetsMock).toHaveBeenCalledWith('strategy-1')

    await wrapper.get('[data-test="symbol-input"]').setValue('BTCUSDT')
    await wrapper.get('[data-test="start-date-input"]').setValue('2024-01-01')
    await wrapper.get('[data-test="end-date-input"]').setValue('2024-01-31')
    await wrapper.get('[data-test="start-backtest"]').trigger('click')
    await flushPromises()

    expect(submitBacktestMock).toHaveBeenCalledWith({
      strategy_id: 'strategy-1',
      symbols: ['BTCUSDT'],
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      parameters: { window: 20 },
    })
    expect(wrapper.text()).toContain('job-1')
  })
})
