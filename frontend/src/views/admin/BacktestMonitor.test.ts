// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const {
  loadQueueStatsMock,
  terminateJobMock,
  toastSuccessMock,
  toastErrorMock,
  storeState
} = vi.hoisted(() => ({
  loadQueueStatsMock: vi.fn(),
  terminateJobMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  storeState: {
    queueStats: {
      pending: 2,
      running: 1,
      avgDuration: 180,
      failureRate1h: 0.25
    },
    stuckJobs: [
      {
        jobId: 'job-1',
        userId: 'user-1',
        strategyId: 'strategy-1',
        strategyName: 'Alpha Strategy',
        startedAt: '2026-03-26T12:00:00+08:00',
        runningDurationSeconds: 901
      }
    ] as any[],
    queueStatsLoading: false,
    terminatingJobs: {} as Record<string, boolean>
  }
}))

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    ...storeState,
    loadQueueStats: loadQueueStatsMock,
    terminateJob: terminateJobMock
  })
}))

vi.mock('../../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock
  }
}))

import BacktestMonitor from './BacktestMonitor.vue'

function mountBacktestMonitor() {
  return mount(BacktestMonitor, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>'
        }
      }
    }
  })
}

describe('BacktestMonitor', () => {
  beforeEach(() => {
    loadQueueStatsMock.mockReset()
    terminateJobMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    storeState.queueStats = {
      pending: 2,
      running: 1,
      avgDuration: 180,
      failureRate1h: 0.25
    }
    storeState.stuckJobs = [
      {
        jobId: 'job-1',
        userId: 'user-1',
        strategyId: 'strategy-1',
        strategyName: 'Alpha Strategy',
        startedAt: '2026-03-26T12:00:00+08:00',
        runningDurationSeconds: 901
      }
    ]
    storeState.queueStatsLoading = false
    storeState.terminatingJobs = {}
  })

  it('loads and renders queue stats with stuck jobs', async () => {
    const wrapper = mountBacktestMonitor()

    expect(loadQueueStatsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.get('[data-test="metric-pending"]').text()).toContain('2')
    expect(wrapper.get('[data-test="metric-running"]').text()).toContain('1')
    expect(wrapper.text()).toContain('Alpha Strategy')

    await wrapper.get('[data-test="monitor-refresh"]').trigger('click')
    expect(loadQueueStatsMock).toHaveBeenCalledTimes(2)
  })

  it('opens the terminate dialog and submits an admin note', async () => {
    terminateJobMock.mockResolvedValueOnce({ jobId: 'job-1', status: 'terminated' })
    const wrapper = mountBacktestMonitor()

    await wrapper.get('[data-test="terminate-job-job-1"]').trigger('click')
    await wrapper.get('[data-test="terminate-note"]').setValue('worker stuck')
    await wrapper.get('[data-test="confirm-terminate"]').trigger('click')
    await flushPromises()

    expect(terminateJobMock).toHaveBeenCalledWith('job-1', 'worker stuck')
    expect(toastSuccessMock).toHaveBeenCalled()
  })
})
