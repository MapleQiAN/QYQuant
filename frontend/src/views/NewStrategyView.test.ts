// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import NewStrategyView from './NewStrategyView.vue'

const { pushMock, analyzeStrategyImportMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  analyzeStrategyImportMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>',
  },
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('../api/strategies', () => ({
  analyzeStrategyImport: analyzeStrategyImportMock,
}))

describe('NewStrategyView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    analyzeStrategyImportMock.mockReset()
    sessionStorage.clear()
  })

  function mountView() {
    return mount(NewStrategyView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                pageTitle: {
                  strategies: 'Strategies',
                },
                common: {
                  close: 'Close',
                },
                strategyNew: {
                  title: 'Create Strategy',
                  subtitle: 'Choose a fast path',
                  back: 'Back',
                  recommendedBadge: 'Recommended',
                  templateTitle: 'Create from template',
                  templateHint: 'Recommended for your first runnable strategy.',
                  templateAction: 'Use a template',
                  templatePickerTitle: 'Choose a starter template',
                  templatePickerSubtitle: 'Start with a runnable example and adjust it later.',
                  templateChecklist: {
                    one: 'one',
                    two: 'two',
                    three: 'three',
                  },
                  importTitle: 'Import existing strategy',
                  importHint: 'Bring your code into the platform.',
                  importNote: 'Analyze before creating',
                  importChecklist: {
                    one: 'one',
                    two: 'two',
                    three: 'three',
                  },
                  importAction: 'Import strategy',
                  guideTitle: 'Writing guide',
                  guideIntro: 'Learn how strategy execution works before you edit code.',
                  guideHint: 'Start with one strategy.py file.',
                  guideExecutionTitle: 'Execution',
                  guideExecutionBody: 'on_bar runs on every bar.',
                  guideExampleTitle: 'Minimal example',
                  guideApiTitle: 'API',
                  guideApiCtx: 'ctx: strategy context',
                  guideApiData: 'data: current bar',
                  guideApiOrder: 'Order: order object',
                  guideErrorsTitle: 'Common mistakes',
                  guideErrorEntrypoint: 'Missing on_bar',
                  guideErrorSyntax: 'Python syntax error',
                  guideErrorReturn: 'Return a list of orders',
                  guideStep1: 'Write an on_bar(ctx, data) function.',
                  guideStep2: 'Save it as strategy.py.',
                  guideStep3: 'Upload the file in the import flow.',
                  guidePrimaryAction: 'Beginner guide',
                  guideSecondaryAction: 'Advanced format',
                  templates: {
                    dualMa: { name: 'Dual MA', description: 'Dual MA desc' },
                    momentum: { name: 'Momentum', description: 'Momentum desc' },
                    meanReversion: { name: 'Mean rev', description: 'Mean rev desc' },
                    blank: { name: 'Blank', description: 'Blank desc' },
                  },
                },
              },
            },
          }),
        ],
      },
    })
  }

  it('analyzes a selected template and routes to import confirmation', async () => {
    analyzeStrategyImportMock.mockResolvedValue({
      draftImportId: 'draft-template-1',
      sourceType: 'python_file',
      entrypointCandidates: [{ path: 'double-moving-average.py', callable: 'on_bar', interface: 'event_v1', confidence: 0.8 }],
      parameterCandidates: [],
      warnings: [],
      errors: [],
      metadataCandidates: {
        name: 'Double Moving Average',
        symbol: 'BTCUSDT',
      },
    })

    const wrapper = mountView()
    await wrapper.get('[data-test="open-template-picker"]').trigger('click')
    await wrapper.get('[data-test="template-card-dual-ma"]').trigger('click')
    await flushPromises()

    expect(analyzeStrategyImportMock).toHaveBeenCalledTimes(1)
    const templateFile = analyzeStrategyImportMock.mock.calls[0]?.[0] as File
    expect(templateFile.name).toBe('double-moving-average.py')
    expect(sessionStorage.getItem('strategy-import:draft-template-1')).toContain('"draftImportId":"draft-template-1"')
    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-import-confirm',
      query: { draftImportId: 'draft-template-1', source: 'template', template: 'dual-ma' },
    })
  })

  it('reveals the merged writing guide content and deep-link actions', async () => {
    const wrapper = mountView()
    expect(wrapper.text()).not.toContain('Write an on_bar(ctx, data) function.')

    await wrapper.get('[data-test="guide-toggle"]').trigger('click')

    expect(wrapper.text()).toContain('Write an on_bar(ctx, data) function.')
    expect(wrapper.text()).toContain('def on_bar(ctx, data):')
    expect(wrapper.text()).toContain('ctx: strategy context')
    expect(wrapper.text()).toContain('Missing on_bar')
    expect(wrapper.get('[data-testid="strategy-guide-primary"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="strategy-guide-secondary"]').exists()).toBe(true)
  })
})
