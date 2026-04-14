import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'
import zh from '../i18n/messages/zh'
import PricingView from './PricingView.vue'

const {
  fetchMyQuotaMock,
  fetchMySubscriptionMock,
  fetchMyOrdersMock,
  getSimBotsMock,
  routerPushMock,
} = vi.hoisted(() => ({
  fetchMyQuotaMock: vi.fn(),
  fetchMySubscriptionMock: vi.fn(),
  fetchMyOrdersMock: vi.fn(),
  getSimBotsMock: vi.fn(),
  routerPushMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPushMock,
  }),
}))

vi.mock('../api/users', async () => {
  const actual = await vi.importActual<typeof import('../api/users')>('../api/users')
  return {
    ...actual,
    fetchMyQuota: fetchMyQuotaMock,
  }
})

vi.mock('../api/payments', async () => {
  const actual = await vi.importActual<typeof import('../api/payments')>('../api/payments')
  return {
    ...actual,
    fetchMySubscription: fetchMySubscriptionMock,
    fetchMyOrders: fetchMyOrdersMock,
  }
})

vi.mock('../api/simulation', async () => {
  const actual = await vi.importActual<typeof import('../api/simulation')>('../api/simulation')
  return {
    ...actual,
    getSimBots: getSimBotsMock,
  }
})

function buildI18n() {
  return createI18n({
    legacy: false,
    globalInjection: true,
    locale: 'zh',
    messages: { zh },
  })
}

function mountView() {
  return mount(PricingView, {
    global: {
      plugins: [buildI18n()],
    },
  })
}

describe('PricingView', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.dataset.theme = 'dark'

    fetchMyQuotaMock.mockReset()
    fetchMySubscriptionMock.mockReset()
    fetchMyOrdersMock.mockReset()
    getSimBotsMock.mockReset()
    routerPushMock.mockReset()

    fetchMyQuotaMock.mockResolvedValue({
      plan_level: 'free',
      used_count: 1,
      plan_limit: 10,
      remaining: 9,
      reset_at: null,
      first_purchase_eligible: true,
    })
    fetchMySubscriptionMock.mockResolvedValue(null)
    fetchMyOrdersMock.mockResolvedValue({
      data: [],
      meta: {
        total: 0,
        page: 1,
        per_page: 10,
      },
    })
    getSimBotsMock.mockResolvedValue([])
  })

  it('shows remaining bot/backtest usage and current plan expiry for logged-in members', async () => {
    localStorage.setItem('qyquant-token', 'token-1')
    fetchMyQuotaMock.mockResolvedValueOnce({
      plan_level: 'pro',
      used_count: 120,
      plan_limit: 500,
      remaining: 380,
      reset_at: null,
      first_purchase_eligible: false,
    })
    fetchMySubscriptionMock.mockResolvedValueOnce({
      id: 'sub-1',
      plan_level: 'pro',
      status: 'active',
      payment_provider: 'alipay',
      starts_at: '2026-04-01T00:00:00+08:00',
      ends_at: '2026-05-01T00:00:00+08:00',
      created_at: '2026-04-01T00:00:00+08:00',
    })
    getSimBotsMock.mockResolvedValueOnce([
      { id: 'bot-1', strategy_id: 's-1', strategy_name: 'A', initial_capital: '1000.00', status: 'active', created_at: '2026-04-01T00:00:00+08:00' },
      { id: 'bot-2', strategy_id: 's-2', strategy_name: 'B', initial_capital: '1000.00', status: 'paused', created_at: '2026-04-01T00:00:00+08:00' },
      { id: 'bot-3', strategy_id: 's-3', strategy_name: 'C', initial_capital: '1000.00', status: 'active', created_at: '2026-04-01T00:00:00+08:00' },
    ])

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('[data-test="usage-bot-remaining"]').text()).toContain('1')
    expect(wrapper.get('[data-test="usage-backtest-remaining"]').text()).toContain('380')
    expect(wrapper.get('[data-test="usage-plan-expiry"]').text()).toContain('2026/05/01')
  })

  it('hides first-purchase promo for users who already have a member plan', async () => {
    localStorage.setItem('qyquant-token', 'token-2')
    fetchMyQuotaMock.mockResolvedValueOnce({
      plan_level: 'plus',
      used_count: 20,
      plan_limit: 200,
      remaining: 180,
      reset_at: null,
      first_purchase_eligible: true,
    })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('.pricing-card__promo-tag')).toHaveLength(0)
  })

  it('shows first-purchase promo for eligible free users', async () => {
    localStorage.setItem('qyquant-token', 'token-3')
    fetchMyQuotaMock.mockResolvedValueOnce({
      plan_level: 'free',
      used_count: 0,
      plan_limit: 10,
      remaining: 10,
      reset_at: null,
      first_purchase_eligible: true,
    })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('.pricing-card__promo-tag').length).toBeGreaterThan(0)
  })

  it('adds a light-mode class to the ultra card', async () => {
    document.documentElement.dataset.theme = 'light'

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('.pricing-card--ultra-light')).toHaveLength(1)
  })

  it('renders localized plan descriptions from i18n-backed plan data', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('适合零基础入门')
    expect(wrapper.text()).not.toContain('閫傚悎')
  })
})
