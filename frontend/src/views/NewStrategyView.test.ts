// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import NewStrategyView from './NewStrategyView.vue'

const {
  pushMock,
  analyzeStrategyImportMock,
  fetchIntegrationsMock,
  createIntegrationMock,
  generateAiStrategyDraftMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  analyzeStrategyImportMock: vi.fn(),
  fetchIntegrationsMock: vi.fn(),
  createIntegrationMock: vi.fn(),
  generateAiStrategyDraftMock: vi.fn(),
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
  generateAiStrategyDraft: generateAiStrategyDraftMock,
}))

vi.mock('../api/integrations', () => ({
  fetchIntegrations: fetchIntegrationsMock,
  createIntegration: createIntegrationMock,
}))

describe('NewStrategyView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    analyzeStrategyImportMock.mockReset()
    fetchIntegrationsMock.mockReset()
    createIntegrationMock.mockReset()
    generateAiStrategyDraftMock.mockReset()
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
                  aiBadge: 'AI',
                  aiTitle: 'Create with AI',
                  aiHint: 'Use AI',
                  aiAction: 'Start AI draft',
                  aiChecklist: {
                    one: 'one',
                    two: 'two',
                    three: 'three',
                  },
                  aiModalTitle: 'AI Strategy Builder',
                  aiModalHint: 'Hint',
                  aiLoading: 'Loading AI connections...',
                  aiConnectionTitle: 'AI connection',
                  aiIntegrationLabel: 'Saved AI connection',
                  aiReuseHint: 'Reuse',
                  aiSetupHint: 'Configure your AI connection in Settings before using AI generation.',
                  aiOpenSettingsAction: 'Open Settings',
                  aiSelectIntegration: 'Select integration',
                  aiDraftTitle: 'Latest draft',
                  aiAdoptAction: 'Use this draft',
                  aiEmptyState: 'Empty',
                  aiUserRole: 'You',
                  aiAssistantRole: 'AI',
                  aiPromptLabel: 'Prompt',
                  aiPromptPlaceholder: 'Describe strategy',
                  aiSendAction: 'Send to AI',
                  aiSending: 'Generating...',
                  aiError: 'AI error',
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

  it('creates AI draft and routes to strategy preview', async () => {
    fetchIntegrationsMock.mockResolvedValue([
      {
        id: 'integration-ai-1',
        providerKey: 'openai_compatible',
        displayName: 'Strategy AI',
        status: 'active',
        configPublic: {},
        lastValidatedAt: null,
        lastSuccessAt: null,
        lastFailureAt: null,
        lastErrorMessage: null,
        createdAt: null,
        updatedAt: null,
      },
    ])
    generateAiStrategyDraftMock.mockResolvedValue({
      reply: 'Draft ready.',
      analysis: {
        draftImportId: 'draft-ai-1',
        sourceType: 'python_file',
        entrypointCandidates: [{ path: 'ai-draft.py', callable: 'on_bar', interface: 'event_v1', confidence: 0.8 }],
        parameterCandidates: [],
        warnings: [],
        errors: [],
        metadataCandidates: {
          name: 'AI Draft',
          symbol: 'BTCUSDT',
          category: 'momentum',
        },
      },
    })

    const wrapper = mountView()
    await wrapper.get('[data-test="open-ai-builder"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-test="ai-prompt"]').setValue('Build a BTC trend strategy')
    await wrapper.get('[data-test="ai-send"]').trigger('click')
    await flushPromises()

    expect(generateAiStrategyDraftMock).toHaveBeenCalledWith({
      integrationId: 'integration-ai-1',
      messages: [{ role: 'user', content: 'Build a BTC trend strategy' }],
    })

    await wrapper.get('[data-test="ai-adopt"]').trigger('click')

    expect(sessionStorage.getItem('strategy-import:draft-ai-1')).toContain('"draftImportId":"draft-ai-1"')
    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-preview',
      query: { draftImportId: 'draft-ai-1', source: 'ai' },
    })
  })

  it('redirects to settings when no AI integration is configured', async () => {
    fetchIntegrationsMock.mockResolvedValue([])

    const wrapper = mountView()
    await wrapper.get('[data-test="open-ai-builder"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Configure your AI connection in Settings before using AI generation.')
    expect(wrapper.find('[data-test="ai-connect-integration"]').exists()).toBe(false)

    await wrapper.get('[data-test="ai-open-settings"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      path: '/settings',
      query: {
        provider: 'openai_compatible',
        redirect: '/strategies/new',
      },
    })
    expect(createIntegrationMock).not.toHaveBeenCalled()
  })
})
