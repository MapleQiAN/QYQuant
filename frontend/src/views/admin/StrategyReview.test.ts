// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const {
  loadPendingReviewsMock,
  loadReviewPacketMock,
  reviewStrategyMock,
  storeState,
  toastSuccessMock,
  toastErrorMock
} = vi.hoisted(() => ({
  loadPendingReviewsMock: vi.fn(),
  loadReviewPacketMock: vi.fn(),
  reviewStrategyMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  storeState: {
    reviewQueue: [
      {
        id: 'strategy-1',
        title: '均线趋势增强版',
        name: 'ma-pro',
        description: '趋势策略描述',
        category: 'trend-following',
        tags: ['均线', '趋势'],
        displayMetrics: {
          sharpe_ratio: 1.45,
          max_drawdown: -8.2,
          total_return: 24.6
        },
        ownerId: 'user-1',
        authorNickname: 'Alice',
        createdAt: '2026-03-23T12:00:00+08:00',
        reviewStatus: 'pending'
      }
    ] as any[],
    reviewQueueLoading: false,
    reviewQueueMeta: { total: 1, page: 1, perPage: 20 },
    reviewSubmitting: {} as Record<string, boolean>,
    reviewPackets: {} as Record<string, any>,
    reviewPacketLoading: {} as Record<string, boolean>
  }
}))

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: () => ({
    ...storeState,
    loadPendingReviews: loadPendingReviewsMock,
    loadReviewPacket: loadReviewPacketMock,
    reviewStrategy: reviewStrategyMock
  })
}))

vi.mock('../../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock
  }
}))

import StrategyReview from './StrategyReview.vue'

function mountStrategyReview() {
  return mount(StrategyReview, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>'
        }
      }
    }
  })
}

describe('StrategyReview', () => {
  beforeEach(() => {
    loadPendingReviewsMock.mockReset()
    loadReviewPacketMock.mockReset()
    reviewStrategyMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    storeState.reviewQueue = [
      {
        id: 'strategy-1',
        title: '均线趋势增强版',
        name: 'ma-pro',
        description: '趋势策略描述',
        category: 'trend-following',
        tags: ['均线', '趋势'],
        displayMetrics: {
          sharpe_ratio: 1.45,
          max_drawdown: -8.2,
          total_return: 24.6
        },
        ownerId: 'user-1',
        authorNickname: 'Alice',
        createdAt: '2026-03-23T12:00:00+08:00',
        reviewStatus: 'pending'
      }
    ]
    storeState.reviewQueueLoading = false
    storeState.reviewQueueMeta = { total: 1, page: 1, perPage: 20 }
    storeState.reviewSubmitting = {}
    storeState.reviewPackets = {}
    storeState.reviewPacketLoading = {}
  })

  it('loads and renders the pending review queue', () => {
    const wrapper = mountStrategyReview()

    expect(loadPendingReviewsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('策略审核队列')
    expect(wrapper.text()).toContain('均线趋势增强版')
    expect(wrapper.text()).toContain('Alice')
  })

  it('approves a strategy and shows success toast', async () => {
    reviewStrategyMock.mockResolvedValueOnce({ strategyId: 'strategy-1', reviewStatus: 'approved' })
    const wrapper = mountStrategyReview()

    await wrapper.get('[data-test="approve-strategy-1"]').trigger('click')
    await flushPromises()

    expect(reviewStrategyMock).toHaveBeenCalledWith('strategy-1', { status: 'approved' })
    expect(toastSuccessMock).toHaveBeenCalledWith('审核已通过')
  })

  it('loads and renders review evidence for a strategy', async () => {
    const packet = {
      version: {
        version: '1.0.0',
        fileId: 'file-1',
        filename: 'ma-pro.qys',
        checksum: 'abc123',
        checksumValid: true
      },
      latestBacktest: {
        id: 'job-1',
        status: 'completed',
        params: { symbol: 'BTCUSDT' },
        resultSummary: { total_return: 24.6, max_drawdown: -8.2 },
        resultStorageKey: 'backtests/job-1'
      },
      checks: {
        hasVersion: true,
        hasPackageFile: true,
        checksumValid: true,
        hasCompletedBacktest: true
      }
    }
    loadReviewPacketMock.mockImplementationOnce(async (strategyId: string) => {
      storeState.reviewPackets[strategyId] = packet
      return packet
    })
    const wrapper = mountStrategyReview()

    await wrapper.get('[data-test="review-evidence-strategy-1"]').trigger('click')
    await flushPromises()
    wrapper.vm.$forceUpdate()
    await wrapper.vm.$nextTick()

    expect(loadReviewPacketMock).toHaveBeenCalledWith('strategy-1')
    expect(wrapper.text()).toContain('ma-pro.qys')
    expect(wrapper.text()).toContain('job-1')
    expect(wrapper.text()).toContain('校验通过')
  })

  it('rejects a strategy with a reason and shows success toast', async () => {
    reviewStrategyMock.mockResolvedValueOnce({ strategyId: 'strategy-1', reviewStatus: 'rejected' })
    const wrapper = mountStrategyReview()

    await wrapper.get('[data-test="reject-reason-strategy-1"]').setValue('风险披露不足')
    await wrapper.get('[data-test="reject-strategy-1"]').trigger('click')
    await flushPromises()

    expect(reviewStrategyMock).toHaveBeenCalledWith('strategy-1', {
      status: 'rejected',
      reason: '风险披露不足'
    })
    expect(toastSuccessMock).toHaveBeenCalledWith('审核已拒绝')
  })

  it('shows error toast when rejecting without a reason', async () => {
    const wrapper = mountStrategyReview()

    await wrapper.get('[data-test="reject-strategy-1"]').trigger('click')
    await flushPromises()

    expect(reviewStrategyMock).not.toHaveBeenCalled()
    expect(toastErrorMock).toHaveBeenCalledWith('请填写拒绝原因')
  })
})
