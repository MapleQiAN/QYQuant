// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import FeaturedStrategyCard from './FeaturedStrategyCard.vue'

describe('FeaturedStrategyCard', () => {
  it('renders title author verified badge and CTA', () => {
    const wrapper = mount(FeaturedStrategyCard, {
      props: {
        strategy: {
          id: 'featured-1',
          title: 'Alpha Momentum Prime',
          name: 'alpha-momentum-prime',
          description: 'A high conviction trend model for gold.',
          category: 'trend',
          tags: ['gold', 'momentum'],
          isVerified: true,
          displayMetrics: {
            annualized_return: 22.8,
            max_drawdown: -7.4,
            sharpe_ratio: 1.62
          },
          author: {
            nickname: 'Market Author',
            avatarUrl: 'https://example.com/avatar.png'
          }
        }
      }
    })

    expect(wrapper.text()).toContain('Alpha Momentum Prime')
    expect(wrapper.text()).toContain('Market Author')
    expect(wrapper.find('[data-test="verified-badge"]').exists()).toBe(true)
    expect(wrapper.get('[data-test="featured-cta"]').text()).toContain('Try backtest')
  })
})
