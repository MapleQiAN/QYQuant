// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StrategyCard from './StrategyCard.vue'

describe('StrategyCard', () => {
  it('renders category tags metrics and author', () => {
    const wrapper = mount(StrategyCard, {
      props: {
        strategy: {
          id: 'strategy-1',
          title: 'Gold Swing Core',
          name: 'gold-swing-core',
          description: 'Swing strategy for daily sessions.',
          category: 'swing',
          tags: ['gold', 'swing'],
          isVerified: false,
          displayMetrics: {
            annualized_return: 14.3,
            max_drawdown: -9.8,
            sharpe_ratio: 1.21
          },
          author: {
            nickname: 'Alice',
            avatarUrl: 'https://example.com/alice.png'
          }
        }
      }
    })

    expect(wrapper.text()).toContain('Gold Swing Core')
    expect(wrapper.text()).toContain('Category: swing')
    expect(wrapper.text()).toContain('gold')
    expect(wrapper.text()).toContain('swing')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.get('[data-test="strategy-cta"]').text()).toContain('Try backtest')
  })
})
