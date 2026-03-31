// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'

const storage = vi.hoisted(() => {
  const values = new Map<string, string>()

  return {
    getItem(key: string) {
      return values.has(key) ? values.get(key)! : null
    },
    setItem(key: string, value: string) {
      values.set(key, value)
    },
    removeItem(key: string) {
      values.delete(key)
    },
    clear() {
      values.clear()
    }
  }
})

Object.defineProperty(globalThis, 'localStorage', {
  value: storage,
  configurable: true,
})

function createTestI18n() {
  return createI18n({
    legacy: false,
    globalInjection: true,
    locale: 'en',
    messages: {
      en: {
        nav: {
          dashboard: 'Dashboard',
          backtests: 'Backtests',
          bots: 'Bots',
          forum: 'Forum'
        },
        pageTitle: {
          dashboard: 'Dashboard',
          backtests: 'Backtests',
          bots: 'Bots',
          forum: 'Forum',
          default: 'QY Quant'
        },
        common: {
          newStrategy: 'New Strategy',
          searchPlaceholder: 'Search strategies, bots, or discussions'
        }
      }
    }
  })
}

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/strategies', component: { template: '<div />' } },
      { path: '/backtests', component: { template: '<div />' } },
      { path: '/bots', component: { template: '<div />' } },
      { path: '/forum', component: { template: '<div />' } },
      { path: '/settings', component: { template: '<div />' } },
    ]
  })
}

async function mountTopNav(
  path = '/',
  setupStore?: (
    userStore: ReturnType<typeof import('../stores/user')['useUserStore']>,
    notificationStore: ReturnType<typeof import('../stores/useNotificationStore')['useNotificationStore']>
  ) => void
) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createTestRouter()
  const i18n = createTestI18n()
  const { default: TopNav } = await import('./TopNav.vue')
  const { useUserStore } = await import('../stores/user')
  const { useNotificationStore } = await import('../stores/useNotificationStore')
  const userStore = useUserStore()
  const notificationStore = useNotificationStore()
  const startPollingSpy = vi.spyOn(notificationStore, 'startPolling').mockImplementation(() => undefined)
  const stopPollingSpy = vi.spyOn(notificationStore, 'stopPolling').mockImplementation(() => undefined)

  if (setupStore) {
    setupStore(userStore, notificationStore)
  }

  await router.push(path)
  await router.isReady()

  const wrapper = mount(TopNav, {
    global: {
      plugins: [pinia, i18n, router]
    }
  })

  return { wrapper, router, notificationStore, startPollingSpy, stopPollingSpy }
}

describe('TopNav', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the header with breadcrumb showing current page', async () => {
    const { wrapper } = await mountTopNav('/backtests')

    expect(wrapper.find('.top-header').exists()).toBe(true)
    expect(wrapper.find('.breadcrumb-current').text()).toBe('Backtests')
  })

  it('opens the help panel when the help button is clicked', async () => {
    const { wrapper } = await mountTopNav()
    const { useUserStore } = await import('../stores/user')
    const userStore = useUserStore()

    const helpBtn = wrapper.findAll('.header-btn').find(btn => btn.attributes('aria-label') === 'Help')
    expect(helpBtn).toBeTruthy()
    await helpBtn!.trigger('click')

    expect(userStore.helpPanelOpen).toBe(true)
  })

  it('shows notification dot and user info from stores', async () => {
    const { wrapper } = await mountTopNav('/', (userStore, notificationStore) => {
      userStore.profile.avatar = 'Q'
      userStore.profile.level = 'PRO'
      notificationStore.unreadCount = 3
    })

    expect(wrapper.find('.notification-dot').exists()).toBe(true)
    expect(wrapper.find('.user-avatar').text()).toBe('Q')
    expect(wrapper.find('.header-actions').exists()).toBe(true)
  })

  it('renders the search box with keyboard shortcut indicator', async () => {
    const { wrapper } = await mountTopNav()

    expect(wrapper.find('.search-input').exists()).toBe(true)
    expect(wrapper.find('.search-kbd').text()).toBe('/')
  })

  it('starts and stops notification polling with component lifecycle', async () => {
    const { wrapper, startPollingSpy, stopPollingSpy } = await mountTopNav()

    expect(startPollingSpy).toHaveBeenCalledTimes(1)

    wrapper.unmount()

    expect(stopPollingSpy).toHaveBeenCalledTimes(1)
  })
})
