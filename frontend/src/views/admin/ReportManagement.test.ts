// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const {
  loadPendingReportsMock,
  resolveReportMock,
  storeState,
  toastSuccessMock,
  toastErrorMock
} = vi.hoisted(() => ({
  loadPendingReportsMock: vi.fn(),
  resolveReportMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  storeState: {
    reportQueue: [
      {
        id: 'report-1',
        reporterId: 'user-2',
        reporterNickname: 'Watcher',
        strategyId: 'strategy-1',
        strategyTitle: 'Alpha Strategy',
        strategyAuthorId: 'user-1',
        strategyAuthorNickname: 'Author',
        reason: 'misleading claim',
        status: 'pending',
        createdAt: '2026-03-26T12:00:00+08:00'
      }
    ] as any[],
    reportQueueLoading: false,
    reportQueueMeta: { total: 1, page: 1, perPage: 20 },
    reportResolving: {} as Record<string, boolean>
  }
}))

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    ...storeState,
    loadPendingReports: loadPendingReportsMock,
    resolveReport: resolveReportMock
  })
}))

vi.mock('../../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock
  }
}))

import ReportManagement from './ReportManagement.vue'

function mountReportManagement() {
  return mount(ReportManagement, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>'
        }
      }
    }
  })
}

describe('ReportManagement', () => {
  beforeEach(() => {
    loadPendingReportsMock.mockReset()
    resolveReportMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    storeState.reportQueue = [
      {
        id: 'report-1',
        reporterId: 'user-2',
        reporterNickname: 'Watcher',
        strategyId: 'strategy-1',
        strategyTitle: 'Alpha Strategy',
        strategyAuthorId: 'user-1',
        strategyAuthorNickname: 'Author',
        reason: 'misleading claim',
        status: 'pending',
        createdAt: '2026-03-26T12:00:00+08:00'
      }
    ]
    storeState.reportQueueLoading = false
    storeState.reportQueueMeta = { total: 1, page: 1, perPage: 20 }
    storeState.reportResolving = {}
  })

  it('loads and renders the pending report queue', () => {
    const wrapper = mountReportManagement()

    expect(loadPendingReportsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('举报管理')
    expect(wrapper.text()).toContain('Alpha Strategy')
    expect(wrapper.text()).toContain('Watcher')
  })

  it('takes down a strategy from a report card', async () => {
    resolveReportMock.mockResolvedValueOnce({ reportId: 'report-1', status: 'reviewed', action: 'takedown' })
    const wrapper = mountReportManagement()

    await wrapper.get('[data-test="admin-note-report-1"]').setValue('compliance issue')
    await wrapper.get('[data-test="takedown-report-1"]').trigger('click')
    await flushPromises()

    expect(resolveReportMock).toHaveBeenCalledWith('report-1', {
      action: 'takedown',
      adminNote: 'compliance issue'
    })
    expect(toastSuccessMock).toHaveBeenCalledWith('已下架相关策略')
  })

  it('dismisses a report card', async () => {
    resolveReportMock.mockResolvedValueOnce({ reportId: 'report-1', status: 'dismissed', action: 'dismiss' })
    const wrapper = mountReportManagement()

    await wrapper.get('[data-test="dismiss-report-1"]').trigger('click')
    await flushPromises()

    expect(resolveReportMock).toHaveBeenCalledWith('report-1', {
      action: 'dismiss',
      adminNote: undefined
    })
    expect(toastSuccessMock).toHaveBeenCalledWith('已驳回举报')
  })
})
