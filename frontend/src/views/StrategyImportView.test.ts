// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import StrategyImportView from './StrategyImportView.vue'

const { pushMock, analyzeStrategyImportMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  analyzeStrategyImportMock: vi.fn()
}))

const { toastSuccessMock, toastErrorMock } = vi.hoisted(() => ({
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>'
  },
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../api/strategies', () => ({
  analyzeStrategyImport: analyzeStrategyImportMock
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  }
}))

describe('StrategyImportView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    analyzeStrategyImportMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
    sessionStorage.clear()
  })

  function mountView() {
    return mount(StrategyImportView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                strategy: {
                  import: {
                    pageTitle: 'Import',
                    pageSubtitle: 'Import strategy',
                    backToLibrary: 'Back',
                    strategySource: 'Source',
                    supportedFormats: 'Formats',
                    analyzeButton: 'Analyze',
                    analyzing: 'Analyzing',
                    chooseSourceFirst: 'Choose a file first',
                    failedToAnalyze: 'Analyze failed',
                  }
                }
              }
            }
          })
        ]
      }
    })
  }

  it('analyzes a selected file and routes to confirmation', async () => {
    analyzeStrategyImportMock.mockResolvedValue({
      draftImportId: 'draft-1',
      sourceType: 'python_file',
      entrypointCandidates: [{ path: 'strategy.py', callable: 'Strategy', interface: 'event_v1', confidence: 0.9 }],
      parameterCandidates: [],
      warnings: [],
      errors: []
    })

    const wrapper = mountView()
    const file = new File(['class Strategy:\n    pass'], 'strategy.py', { type: 'text/x-python' })
    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [file]
    })
    await input.trigger('change')
    await wrapper.get('button.btn.btn-primary').trigger('click')
    await flushPromises()

    expect(analyzeStrategyImportMock).toHaveBeenCalledTimes(1)
    expect(analyzeStrategyImportMock.mock.calls[0]?.[0]?.name).toBe('strategy.py')
    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-import-confirm',
      query: { draftImportId: 'draft-1' }
    })
    expect(sessionStorage.getItem('strategy-import:draft-1')).toContain('"draftImportId":"draft-1"')
    expect(toastSuccessMock).toHaveBeenCalledWith('导入分析已生成')
  })
})
