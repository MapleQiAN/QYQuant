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
          learnSection: 'Learn',
          forum: 'Forum',
          marketplace: 'Marketplace',
          overview: 'Overview',
          community: 'Community',
          learn: 'Quant Course'
        },
        common: {
          newStrategy: 'New Strategy',
          settings: 'Settings',
          expandSidebar: 'Expand sidebar',
          collapseSidebar: 'Collapse sidebar',
          premiumMember: 'Premium',
          basicPlan: 'Basic',
          manage: 'Manage',
          upgrade: 'Upgrade'
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
      { path: '/learn', component: { template: '<div />' } },
      { path: '/strategies', component: { template: '<div />' } },
      { path: '/backtests', component: { template: '<div />' } },
      { path: '/bots', component: { template: '<div />' } },
      { path: '/forum', component: { template: '<div />' } },
      { path: '/marketplace', component: { template: '<div />' } },
      { path: '/settings', component: { template: '<div />' } },
      { path: '/pricing', component: { template: '<div />' } },
    ]
  })
}

describe('SideNav', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    storage.clear()
  })

  it('renders a dedicated learn section under community with one quant course item', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createTestRouter()
    const i18n = createTestI18n()
    const { default: SideNav } = await import('./SideNav.vue')

    await router.push('/')
    await router.isReady()

    const wrapper = mount(SideNav, {
      props: { collapsed: false },
      global: {
        plugins: [pinia, i18n, router]
      }
    })

    const navLabels = wrapper.findAll('.nav-item-label').map(node => node.text())

    const sectionLabels = wrapper.findAll('.nav-section-label').map(node => node.text())

    expect(sectionLabels).toEqual(['Overview', 'Community', 'Learn'])
    expect(navLabels.filter(label => label === 'Quant Course')).toHaveLength(1)
    expect(wrapper.text()).toContain('Quant Course')
  })
})
