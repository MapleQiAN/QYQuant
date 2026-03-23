import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PricingView from './PricingView.vue'

const {
  fetchMyQuotaMock,
  createPaymentOrderMock,
  windowOpenMock,
} = vi.hoisted(() => ({
  fetchMyQuotaMock: vi.fn(),
  createPaymentOrderMock: vi.fn(),
  windowOpenMock: vi.fn(),
}))

vi.mock('../api/users', () => ({
  fetchMyQuota: fetchMyQuotaMock,
}))

vi.mock('../api/payments', () => ({
  createPaymentOrder: createPaymentOrderMock,
}))

describe('PricingView', () => {
  beforeEach(() => {
    fetchMyQuotaMock.mockReset()
    createPaymentOrderMock.mockReset()
    windowOpenMock.mockReset()

    fetchMyQuotaMock.mockResolvedValue({
      plan_level: 'free',
      used_count: 1,
      plan_limit: 10,
      remaining: 9,
      reset_at: null,
    })

    createPaymentOrderMock.mockResolvedValue({
      order_id: 'ord-100',
      pay_url: 'https://pay.mock.example.com/alipay/pro?amount=500',
      plan_level: 'pro',
      amount: 500,
      provider: 'alipay',
    })

    vi.stubGlobal('open', windowOpenMock)
  })

  it('renders all plans and marks current plan', async () => {
    const wrapper = mount(PricingView)

    await flushPromises()

    const cards = wrapper.findAll('.pricing-card')
    expect(cards).toHaveLength(4)
    expect(wrapper.text()).toContain('当前套餐')
    expect(cards[0].text()).toContain('免费')
    expect(cards[0].text()).not.toContain('微信支付')
  })

  it('creates an order and opens alipay after confirmation', async () => {
    const wrapper = mount(PricingView)

    await flushPromises()

    const buttons = wrapper.findAll('button')
    const alipayButton = buttons.find((button) => button.text() === '支付宝')
    expect(alipayButton).toBeDefined()

    await alipayButton!.trigger('click')
    await flushPromises()

    expect(createPaymentOrderMock).toHaveBeenCalledWith({
      plan_level: 'lite',
      provider: 'alipay',
    })
    expect(wrapper.text()).toContain('确认支付')

    const confirmButton = wrapper.findAll('button').find((button) => button.text() === '确认并前往支付')
    expect(confirmButton).toBeDefined()

    await confirmButton!.trigger('click')

    expect(windowOpenMock).toHaveBeenCalledWith(
      'https://pay.mock.example.com/alipay/pro?amount=500',
      '_blank',
      'noopener'
    )
  })
})
