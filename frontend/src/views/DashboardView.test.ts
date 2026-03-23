import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zh from '../i18n/messages/zh'
import DashboardView from './DashboardView.vue'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  },
  useRouter: () => ({
    push: pushMock
  })
}))

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
    profile: { id: 'user-1', name: '测试用户', onboarding_completed: true },
    guidedBacktestActive: false,
    loadProfile: vi.fn(),
    markOnboardingCompleted: vi.fn(),
    setOnboardingHighlightTarget: vi.fn(),
    startGuidedBacktest: vi.fn()
  })
}))

vi.mock('../stores/useSimulationStore', () => ({
  useSimulationStore: () => ({
    pauseBot: vi.fn(),
    resumeBot: vi.fn()
  })
}))

describe('DashboardView', () => {
  beforeEach(() => {
    pushMock.mockReset()
  })

  it('renders localized header', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      globalInjection: true,
      messages: { zh }
    })

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [i18n],
        stubs: {
          BacktestCard: {
            template: '<div data-test="backtest-card" />'
          }
        }
      }
    })

    expect(wrapper.text()).toContain('欢迎回来')
  })

  it('routes dashboard child actions to their target pages', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      globalInjection: true,
      messages: { zh }
    })

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [i18n],
        stubs: {
          BacktestCard: {
            template: '<div data-test="backtest-card" />'
          },
          RecentList: {
            template: `
              <div>
                <button data-test="strategy-action" @click="$emit('open-strategy', 'strategy-1')" />
                <button data-test="deploy-action" @click="$emit('deploy-strategy', 'strategy-1')" />
                <button data-test="bot-action" @click="$emit('open-bot', 'bot-1')" />
                <button data-test="view-all-bots" @click="$emit('view-all', 'bots')" />
              </div>
            `
          },
          ForumMiniCard: {
            template: `
              <div>
                <button data-test="forum-publish" @click="$emit('publish')" />
                <button data-test="forum-bookmarks" @click="$emit('bookmarks')" />
              </div>
            `
          },
          UpgradeCard: {
            template: '<button data-test="upgrade-card" @click="$emit(\'upgrade\')" />'
          }
        }
      }
    })

    await wrapper.get('[data-test="strategy-action"]').trigger('click')
    await wrapper.get('[data-test="deploy-action"]').trigger('click')
    await wrapper.get('[data-test="bot-action"]').trigger('click')
    await wrapper.get('[data-test="view-all-bots"]').trigger('click')
    await wrapper.get('[data-test="forum-publish"]').trigger('click')
    await wrapper.get('[data-test="forum-bookmarks"]').trigger('click')
    await wrapper.get('[data-test="upgrade-card"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({ name: 'strategy-parameters', params: { strategyId: 'strategy-1' } })
    expect(pushMock).toHaveBeenCalledWith({ name: 'bots', query: { create: '1', strategyId: 'strategy-1' } })
    expect(pushMock).toHaveBeenCalledWith({ name: 'bots', query: { botId: 'bot-1', modal: 'detail' } })
    expect(pushMock).toHaveBeenCalledWith({ name: 'bots' })
    expect(pushMock).toHaveBeenCalledWith({ name: 'forum', query: { compose: '1' } })
    expect(pushMock).toHaveBeenCalledWith({ name: 'forum', query: { view: 'collections' } })
    expect(pushMock).toHaveBeenCalledWith({ name: 'pricing' })
  })
})
