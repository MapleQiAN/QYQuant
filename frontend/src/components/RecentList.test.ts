// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import RecentList from './RecentList.vue'

describe('RecentList', () => {
  it('emits strategy actions and routes the footer CTA from strategy tab', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: { en: {} },
      missingWarn: false,
      fallbackWarn: false
    })

    const wrapper = mount(RecentList, {
      props: {
        strategies: [
          {
            id: 'strategy-1',
            name: 'Gold swing',
            symbol: 'XAUUSD',
            status: 'running',
            returns: 18,
            winRate: 62,
            maxDrawdown: -7,
            tags: ['gold'],
            lastUpdate: '2026-03-20',
            trades: 24
          }
        ]
      },
      global: {
        plugins: [i18n]
      }
    })

    await wrapper.get('.item-main').trigger('click')
    await wrapper.get('[data-test="recent-strategy-detail-strategy-1"]').trigger('click')
    await wrapper.get('[data-test="recent-strategy-deploy-strategy-1"]').trigger('click')
    await wrapper.get('[data-test="recent-view-all"]').trigger('click')

    expect(wrapper.emitted('open-strategy')).toEqual([['strategy-1']])
    expect(wrapper.emitted('deploy-strategy')).toEqual([['strategy-1']])
    expect(wrapper.emitted('view-all')).toEqual([['strategies']])
  })

  it('emits bot actions from the bots tab', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: { en: {} },
      missingWarn: false,
      fallbackWarn: false
    })

    const wrapper = mount(RecentList, {
      props: {
        bots: [
          {
            id: 'bot-1',
            name: 'Gold bot',
            strategy: 'Gold swing',
            status: 'active',
            profit: 3200,
            runtime: '5d',
            capital: 100000,
            tags: ['gold']
          }
        ]
      },
      global: {
        plugins: [i18n]
      }
    })

    await wrapper.get('[data-test="recent-tab-bots"]').trigger('click')
    await wrapper.get('.item-main').trigger('click')
    await wrapper.get('[data-test="recent-bot-detail-bot-1"]').trigger('click')
    await wrapper.get('[data-test="recent-bot-toggle-bot-1"]').trigger('click')
    await wrapper.get('[data-test="recent-view-all"]').trigger('click')

    expect(wrapper.emitted('open-bot')).toEqual([['bot-1']])
    expect(wrapper.emitted('toggle-bot')).toEqual([['bot-1', 'pause']])
    expect(wrapper.emitted('view-all')).toEqual([['bots']])
  })
})
