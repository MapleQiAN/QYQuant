// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyPublishFlow from './StrategyPublishFlow.vue'

describe('StrategyPublishFlow', () => {
  it('blocks submit until the agreement checkbox is checked', async () => {
    const wrapper = mount(StrategyPublishFlow, {
      props: {
        open: true,
        strategy: {
          id: 'strategy-1',
          name: '均线策略',
          title: '均线策略',
          description: 'desc',
          category: 'trend-following',
          reviewStatus: 'draft',
          returns: 12.5,
          maxDrawdown: -8.2,
          tags: ['均线'],
          symbol: 'BTCUSDT',
          status: 'draft',
          winRate: 0,
          lastUpdate: 0,
          trades: 0
        },
        submitting: false,
        submitted: false,
        submitError: ''
      }
    })

    await wrapper.get('[data-test="publish-title"]').setValue('均线趋势增强版')
    await wrapper.get('[data-test="publish-description"]').setValue('desc')
    await wrapper.get('[data-test="publish-tags"]').setValue('均线, 趋势')
    await wrapper.get('[data-test="publish-sharpe-ratio"]').setValue('1.45')
    await wrapper.get('[data-test="publish-max-drawdown"]').setValue('-8.2')
    await wrapper.get('[data-test="publish-total-return"]').setValue('28.4')
    await wrapper.get('[data-test="publish-next"]').trigger('click')

    expect(wrapper.get('[data-test="publish-confirm"]').attributes('disabled')).toBeDefined()

    await wrapper.get('[data-test="publish-agreement"]').setValue(true)
    await wrapper.get('[data-test="publish-confirm"]').trigger('click')

    expect(wrapper.emitted('submit')?.[0]?.[0]).toMatchObject({
      strategyId: 'strategy-1',
      title: '均线趋势增强版',
      description: 'desc',
      tags: ['均线', '趋势'],
      category: 'trend-following',
      displayMetrics: {
        sharpe_ratio: 1.45,
        max_drawdown: -8.2,
        total_return: 28.4
      }
    })
  })

  it('shows success step after submission completes', async () => {
    const wrapper = mount(StrategyPublishFlow, {
      props: {
        open: true,
        strategy: {
          id: 'strategy-1',
          name: '均线策略',
          title: '均线策略',
          description: 'desc',
          category: 'trend-following',
          reviewStatus: 'draft',
          returns: 12.5,
          maxDrawdown: -8.2,
          tags: ['均线'],
          symbol: 'BTCUSDT',
          status: 'draft',
          winRate: 0,
          lastUpdate: 0,
          trades: 0
        },
        submitting: false,
        submitted: false,
        submitError: ''
      }
    })

    await wrapper.setProps({ submitted: true })
    await flushPromises()

    expect(wrapper.text()).toContain('submitted for review')
  })
})
