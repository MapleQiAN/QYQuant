// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import en from '../i18n/messages/en'
import AiStrategyLabView from './AiStrategyLabView.vue'

const {
  pushMock,
  fetchIntegrationsMock,
  generateAiStrategyDraftMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  fetchIntegrationsMock: vi.fn(),
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

vi.mock('../api/integrations', () => ({
  fetchIntegrations: fetchIntegrationsMock,
}))

vi.mock('../api/strategies', () => ({
  generateAiStrategyDraft: generateAiStrategyDraftMock,
}))

vi.mock('../stores/user', () => ({
  useUserStore: () => ({
    locale: 'en',
  }),
}))

describe('AiStrategyLabView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    fetchIntegrationsMock.mockReset()
    generateAiStrategyDraftMock.mockReset()
    sessionStorage.clear()
  })

  function mountView() {
    return mount(AiStrategyLabView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: { en },
          }),
        ],
      },
    })
  }

  it('shows setup state when no AI integration is configured', async () => {
    fetchIntegrationsMock.mockResolvedValue([])

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('AI connection required')

    await wrapper.get('[data-test="ai-lab-open-settings"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      path: '/settings',
      query: {
        provider: 'openai_compatible',
        redirect: '/strategies/ai-lab',
      },
    })
  })

  it('generates a draft and renders the verified draft panel', async () => {
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
        parameterCandidates: [
          {
            key: 'lookback',
            type: 'integer',
            default: 20,
            user_facing: {
              label: 'Lookback',
              group: 'Signal',
            },
          },
        ],
        warnings: [],
        errors: [],
        metadataCandidates: {
          name: 'AI Draft',
          symbol: 'BTCUSDT',
          timeframe: '1d',
          riskLevel: 'medium',
          logicExplanation: 'Follow trend after confirmation.',
          riskRules: 'Stop when drawdown limit is hit.',
        },
      },
    })

    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="ai-lab-prompt"]').setValue('Build a BTC trend strategy')
    await wrapper.get('[data-test="ai-lab-generate"]').trigger('click')
    await flushPromises()

    expect(generateAiStrategyDraftMock).toHaveBeenCalledTimes(1)
    expect(generateAiStrategyDraftMock.mock.calls[0][0].integrationId).toBe('integration-ai-1')
    expect(generateAiStrategyDraftMock.mock.calls[0][0].locale).toBe('en')
    expect(generateAiStrategyDraftMock.mock.calls[0][0].messages[0].content).toContain('Symbol: BTCUSDT')
    expect(generateAiStrategyDraftMock.mock.calls[0][0].messages[0].content).toContain('Additional request: Build a BTC trend strategy')
    expect(wrapper.text()).toContain('AI Draft')
    expect(wrapper.text()).toContain('Lookback')
    expect(wrapper.get('[data-test="ai-lab-adopt"]').attributes('disabled')).toBeUndefined()
  })

  it('adopts a generated draft into the existing preview flow', async () => {
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
        },
      },
    })

    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="ai-lab-prompt"]').setValue('Build a BTC trend strategy')
    await wrapper.get('[data-test="ai-lab-generate"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-test="ai-lab-adopt"]').trigger('click')

    expect(sessionStorage.getItem('strategy-import:draft-ai-1')).toContain('"draftImportId":"draft-ai-1"')
    expect(pushMock).toHaveBeenCalledWith({
      name: 'strategy-preview',
      query: {
        draftImportId: 'draft-ai-1',
        source: 'ai',
      },
    })
  })
})

