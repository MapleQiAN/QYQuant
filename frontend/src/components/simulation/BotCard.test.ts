// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BotCard from './BotCard.vue'
import type { SimulationBot } from '../../types/Simulation'

const makeBot = (overrides: Partial<SimulationBot> = {}): SimulationBot => ({
  id: 'bot-1',
  strategy_id: 'strategy-1',
  strategy_name: '双均线策略',
  initial_capital: '100000.00',
  status: 'active',
  created_at: '2026-03-23T16:00:00+08:00',
  ...overrides,
})

describe('BotCard', () => {
  it('renders strategy_name', () => {
    const wrapper = mount(BotCard, { props: { bot: makeBot() } })
    expect(wrapper.text()).toContain('双均线策略')
  })

  it('shows 运行中 for active status', () => {
    const wrapper = mount(BotCard, { props: { bot: makeBot({ status: 'active' }) } })
    expect(wrapper.text()).toContain('运行中')
  })

  it('shows 已暂停 for paused status', () => {
    const wrapper = mount(BotCard, { props: { bot: makeBot({ status: 'paused' }) } })
    expect(wrapper.text()).toContain('已暂停')
  })

  it('shows 已停止 for stopped status', () => {
    const wrapper = mount(BotCard, { props: { bot: makeBot({ status: 'stopped' }) } })
    expect(wrapper.text()).toContain('已停止')
  })

  it('displays initial_capital formatted', () => {
    const wrapper = mount(BotCard, { props: { bot: makeBot({ initial_capital: '100000.00' }) } })
    expect(wrapper.text()).toContain('100,000')
  })

  it('emits view-positions with bot.id when button clicked', async () => {
    const bot = makeBot()
    const wrapper = mount(BotCard, { props: { bot } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('view-positions')).toEqual([['bot-1']])
  })
})
