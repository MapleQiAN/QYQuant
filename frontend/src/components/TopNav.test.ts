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

  if (setupStore) {
    setupStore(useUserStore(), useNotificationStore())
  }

  await router.push(path)
  await router.isReady()

  const wrapper = mount(TopNav, {
    global: {
      plugins: [pinia, i18n, router]
    }
  })

  return { wrapper, router }
}

describe('TopNav', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders all primary navigation links and marks the current route active', async () => {
    const { wrapper } = await mountTopNav('/backtests')

    expect(wrapper.findAll('.nav-link')).toHaveLength(5)
    expect(wrapper.findAll('.nav-link.active')).toHaveLength(1)
    expect(wrapper.find('.nav-link.active').text()).toContain('Backtests')
    expect(wrapper.find('.nav-links-shell').exists()).toBe(true)
  })

  it('opens the help panel when the help button is clicked', async () => {
    const { wrapper } = await mountTopNav()
    const { useUserStore } = await import('../stores/user')
    const userStore = useUserStore()

    await wrapper.get('button[aria-label="打开帮助中心"]').trigger('click')

    expect(userStore.helpPanelOpen).toBe(true)
  })

  it('shows notifications and profile summary from the user store', async () => {
    const { wrapper } = await mountTopNav('/', (userStore, notificationStore) => {
      userStore.profile.avatar = 'Q'
      userStore.profile.level = 'PRO'
      notificationStore.unreadCount = 3
      vi.spyOn(notificationStore, 'startPolling').mockImplementation(() => undefined)
      vi.spyOn(notificationStore, 'stopPolling').mockImplementation(() => undefined)
    })

    expect(wrapper.find('.notification-badge').text()).toBe('3')
    expect(wrapper.find('.avatar-text').text()).toBe('Q')
    expect(wrapper.find('.user-level').text()).toBe('PRO')
    expect(wrapper.find('.nav-actions').exists()).toBe(true)
  })

  it('applies the onboarding highlight class to the targeted nav item', async () => {
    const { wrapper } = await mountTopNav('/strategies', (userStore) => {
      userStore.setOnboardingHighlightTarget('strategy-library-entry')
    })

    expect(wrapper.find('[data-onboarding-target="strategy-library-entry"]').classes()).toContain('onboarding-highlight')
  })

  it('starts and stops notification polling with component lifecycle', async () => {
    const { useNotificationStore } = await import('../stores/useNotificationStore')
    const notificationStore = useNotificationStore()
    const startPollingSpy = vi.spyOn(notificationStore, 'startPolling').mockImplementation(() => undefined)
    const stopPollingSpy = vi.spyOn(notificationStore, 'stopPolling').mockImplementation(() => undefined)

    const { wrapper } = await mountTopNav()

    expect(startPollingSpy).toHaveBeenCalledTimes(1)

    wrapper.unmount()

    expect(stopPollingSpy).toHaveBeenCalledTimes(1)
  })
})
