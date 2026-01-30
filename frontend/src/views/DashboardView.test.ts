import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zh from '../i18n/messages/zh'
import DashboardView from './DashboardView.vue'

vi.mock('../stores', () => ({
  useBacktestsStore: () => ({
    latest: { summary: { totalReturn: 12 }, kline: [], trades: [] },
    loading: false,
    error: null,
    loadLatest: vi.fn()
  }),
  useBotsStore: () => ({
    recent: [],
    loading: false,
    error: null,
    loadRecent: vi.fn()
  }),
  useStrategiesStore: () => ({
    recent: [],
    loading: false,
    error: null,
    loadRecent: vi.fn()
  }),
  useForumStore: () => ({
    posts: [],
    loading: false,
    error: null,
    loadHot: vi.fn()
  }),
  useUserStore: () => ({
    profile: { name: '测试用户' }
  })
}))

describe('DashboardView', () => {
  it('renders localized header', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      globalInjection: true,
      messages: { zh }
    })

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.text()).toContain('欢迎回来')
  })
})
