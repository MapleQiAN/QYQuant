// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const { loadDataSourceHealthMock, storeState } = vi.hoisted(() => ({
  loadDataSourceHealthMock: vi.fn(),
  storeState: {
    dataSourceHealth: {
      sourceName: 'jqdata',
      status: 'unhealthy',
      statusLabel: '异常',
      statusColor: 'red',
      lastCheckedAt: '2026-03-27T09:00:00+08:00',
      lastSuccessAt: '2026-03-27T08:30:00+08:00',
      lastFailureAt: '2026-03-27T09:00:00+08:00',
      lastErrorMessage: 'request timed out',
      consecutiveFailures: 2
    },
    dataSourceHealthLoading: false
  }
}))

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    ...storeState,
    loadDataSourceHealth: loadDataSourceHealthMock
  })
}))

import DataSourceHealth from './DataSourceHealth.vue'

describe('DataSourceHealth', () => {
  beforeEach(() => {
    loadDataSourceHealthMock.mockReset()
    storeState.dataSourceHealth = {
      sourceName: 'jqdata',
      status: 'unhealthy',
      statusLabel: '异常',
      statusColor: 'red',
      lastCheckedAt: '2026-03-27T09:00:00+08:00',
      lastSuccessAt: '2026-03-27T08:30:00+08:00',
      lastFailureAt: '2026-03-27T09:00:00+08:00',
      lastErrorMessage: 'request timed out',
      consecutiveFailures: 2
    }
    storeState.dataSourceHealthLoading = false
  })

  it('loads and renders persisted data source health state', () => {
    const wrapper = mount(DataSourceHealth)

    expect(loadDataSourceHealthMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('JQData')
    expect(wrapper.text()).toContain('异常')
    expect(wrapper.text()).toContain('request timed out')
    expect(wrapper.get('[data-test="data-source-status"]').classes()).toContain('status-pill--red')
  })

  it('allows manual refresh', async () => {
    const wrapper = mount(DataSourceHealth)

    await wrapper.get('[data-test="data-source-refresh"]').trigger('click')
    await flushPromises()

    expect(loadDataSourceHealthMock).toHaveBeenCalledTimes(2)
  })
})
