// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BotPositionsModal from './BotPositionsModal.vue'

const { fetchPositionsMock } = vi.hoisted(() => ({
  fetchPositionsMock: vi.fn().mockResolvedValue([]),
}))

vi.mock('../../stores/useSimulationStore', () => ({
  useSimulationStore: () => ({
    fetchPositions: fetchPositionsMock,
  }),
}))

describe('BotPositionsModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchPositionsMock.mockClear()
    fetchPositionsMock.mockResolvedValue([])
  })

  it('calls fetchPositions with botId on mount', async () => {
    mount(BotPositionsModal, { props: { botId: 'bot-42' } })
    await flushPromises()

    expect(fetchPositionsMock).toHaveBeenCalledWith('bot-42')
  })

  it('shows empty message when no positions', async () => {
    fetchPositionsMock.mockResolvedValueOnce([])

    const wrapper = mount(BotPositionsModal, { props: { botId: 'bot-1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('暂无持仓')
  })

  it('renders positions table when positions returned', async () => {
    fetchPositionsMock.mockResolvedValueOnce([
      {
        symbol: '000001.XSHG',
        quantity: '1000.0000',
        avg_cost: '52.0000',
        updated_at: '2026-03-22T16:00:00+08:00',
      },
    ])

    const wrapper = mount(BotPositionsModal, { props: { botId: 'bot-1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('000001.XSHG')
    expect(wrapper.text()).toContain('1000.0000')
    expect(wrapper.text()).toContain('52.0000')
    expect(wrapper.find('table').exists()).toBe(true)
  })

  it('emits close when overlay background is clicked', async () => {
    const wrapper = mount(BotPositionsModal, { props: { botId: 'bot-1' } })
    await flushPromises()

    await wrapper.find('.modal-overlay').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close when close button is clicked', async () => {
    const wrapper = mount(BotPositionsModal, { props: { botId: 'bot-1' } })
    await flushPromises()

    await wrapper.find('.modal-close').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
