import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const loadOverviewMock = vi.fn()

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    overview: { status: 'ok', scope: 'admin' },
    loading: false,
    loadOverview: loadOverviewMock
  })
}))

import AdminDashboard from './AdminDashboard.vue'

describe('AdminDashboard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    loadOverviewMock.mockReset()
  })

  it('renders admin overview placeholders', () => {
    const wrapper = mount(AdminDashboard, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>'
          }
        }
      }
    })

    expect(wrapper.text()).toContain('管理后台')
    expect(wrapper.text()).toContain('系统概览')
    expect(wrapper.text()).toContain('admin')
    expect(wrapper.find('[data-test="admin-data-source-health-link"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="admin-backtest-monitor-link"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="admin-user-management-link"]').exists()).toBe(true)
    expect(loadOverviewMock).toHaveBeenCalledTimes(1)
  })
})
