// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyImportConfirmView from './StrategyImportConfirmView.vue'

const { pushMock, confirmStrategyImportMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  confirmStrategyImportMock: vi.fn()
}))

const { toastSuccessMock, toastErrorMock } = vi.hoisted(() => ({
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  },
  useRoute: () => ({
    query: { draftImportId: 'draft-1' }
  }),
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../api/strategies', () => ({
  confirmStrategyImport: confirmStrategyImportMock
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  }
}))

describe('StrategyImportConfirmView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    confirmStrategyImportMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    sessionStorage.clear()
    sessionStorage.setItem(
      'strategy-import:draft-1',
      JSON.stringify({
        draftImportId: 'draft-1',
        sourceType: 'python_file',
        fileSummary: {
          filename: 'strategy.py',
          size: 128,
          entries: ['strategy.py']
        },
        entrypointCandidates: [
          {
            path: 'strategy.py',
            callable: 'Strategy',
            interface: 'event_v1',
            confidence: 0.9
          }
        ],
        metadataCandidates: {
          name: 'Detected Strategy',
          description: 'Recovered from README',
          category: 'trend-following',
          symbol: 'XAUUSD',
          tags: ['gold', 'trend']
        },
        parameterCandidates: [{ key: 'window', type: 'integer', default: 20 }],
        warnings: [],
        errors: []
      })
    )
  })

  it('submits confirmation payload and routes to the parameter page', async () => {
    confirmStrategyImportMock.mockResolvedValue({
      strategy: {
        id: 'strategy-1',
        name: 'Detected Strategy'
      },
      next: '/strategies/strategy-1/parameters'
    })

    const wrapper = mount(StrategyImportConfirmView)
    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(confirmStrategyImportMock).toHaveBeenCalledWith({
      draftImportId: 'draft-1',
      selectedEntrypoint: {
        path: 'strategy.py',
        callable: 'Strategy',
        interface: 'event_v1'
      },
      metadata: {
        name: 'Detected Strategy',
        description: 'Recovered from README',
        category: 'trend-following',
        symbol: 'XAUUSD',
        tags: ['gold', 'trend']
      },
      parameterDefinitions: [{ key: 'window', type: 'integer', default: 20 }]
    })
    expect(pushMock).toHaveBeenCalledWith('/strategies/strategy-1/parameters')
    expect(sessionStorage.getItem('strategy-import:draft-1')).toBeNull()
    expect(toastSuccessMock).toHaveBeenCalledWith('策略已导入：Detected Strategy')
  })
})
