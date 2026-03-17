// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GuidedBacktestFlow from './GuidedBacktestFlow.vue'

const { fetchMarketplaceStrategiesMock } = vi.hoisted(() => ({
  fetchMarketplaceStrategiesMock: vi.fn(),
}))

vi.mock('../../api/strategies', async () => {
  const actual = await vi.importActual<typeof import('../../api/strategies')>('../../api/strategies')
  return {
    ...actual,
    fetchMarketplaceStrategies: fetchMarketplaceStrategiesMock,
  }
})

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

describe('GuidedBacktestFlow', () => {
  beforeEach(() => {
    fetchMarketplaceStrategiesMock.mockReset()
    fetchMarketplaceStrategiesMock.mockResolvedValue([
      {
        id: 'guided-strategy',
        name: 'Guided Gold Strategy',
        symbol: 'XAUUSD',
        status: 'running',
        returns: 12.5,
        winRate: 68,
        maxDrawdown: 9.8,
        tags: ['onboarding'],
        trades: 18,
      },
    ])
  })

  it('loads onboarding marketplace strategies and lets the user exit', async () => {
    const wrapper = mount(GuidedBacktestFlow)
    await flushPromises()

    expect(fetchMarketplaceStrategiesMock).toHaveBeenCalledWith({ tag: 'onboarding' })
    expect(wrapper.text()).toContain('Guided Gold Strategy')

    await wrapper.get('[data-test="guided-exit"]').trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
  })
})
