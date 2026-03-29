// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StrategyImportView from './StrategyImportView.vue'

const { pushMock, analyzeStrategyImportMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  analyzeStrategyImportMock: vi.fn()
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

describe('StrategyImportView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    analyzeStrategyImportMock.mockReset()
    sessionStorage.clear()
  })

  it('analyzes a selected file and routes to confirmation', async () => {
    analyzeStrategyImportMock.mockResolvedValue({
      draftImportId: 'draft-1',
      sourceType: 'python_file',
      entrypointCandidates: [{ path: 'strategy.py', callable: 'Strategy', interface: 'event_v1', confidence: 0.9 }],
      parameterCandidates: [],
      warnings: [],
      errors: []
    })

    const wrapper = mount(StrategyImportView)
    const file = new File(['class Strategy:\n    pass'], 'strategy.py', { type: 'text/x-python' })
    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      value: [file]
    })
    await input.trigger('change')
    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(analyzeStrategyImportMock).toHaveBeenCalledWith(file)
    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-import-confirm',
      query: { draftImportId: 'draft-1' }
    })
    expect(sessionStorage.getItem('strategy-import:draft-1')).toContain('"draftImportId":"draft-1"')
  })
})
