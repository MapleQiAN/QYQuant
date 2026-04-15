// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import StrategyImportConfirmView from './StrategyImportConfirmView.vue'

const { pushMock, confirmStrategyImportMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  confirmStrategyImportMock: vi.fn(),
}))

const routeState = vi.hoisted(() => ({
  query: {
    draftImportId: 'draft-1',
    source: 'template',
    template: 'dual-ma',
  } as Record<string, string>,
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    template: '<a><slot /></a>',
  },
  useRoute: () => routeState,
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('../api/strategies', () => ({
  confirmStrategyImport: confirmStrategyImportMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('StrategyImportConfirmView redesign', () => {
  beforeEach(() => {
    pushMock.mockReset()
    confirmStrategyImportMock.mockReset()
    sessionStorage.clear()
    sessionStorage.setItem(
      'strategy-import:draft-1',
      JSON.stringify({
        draftImportId: 'draft-1',
        sourceType: 'python_file',
        fileSummary: {
          filename: 'double-moving-average.py',
          size: 256,
          entries: ['double-moving-average.py'],
        },
        entrypointCandidates: [
          {
            path: 'double-moving-average.py',
            callable: 'on_bar',
            interface: 'event_v1',
            confidence: 0.8,
          },
        ],
        metadataCandidates: {
          name: 'Double Moving Average',
          description: 'Starter template',
          category: 'trend-following',
          symbol: 'BTCUSDT',
          tags: ['template', 'trend'],
        },
        parameterCandidates: [],
        warnings: [],
        errors: [],
        validation: {
          entrypointFound: true,
          pythonSyntaxValid: true,
          orderListReturnLikely: true,
          metadataDetected: true,
        },
      })
    )
  })

  function mountView() {
    return mount(StrategyImportConfirmView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                strategy: {
                  publish: {
                    descriptionLabel: 'Description',
                  },
                  import: {
                    pageTitle: 'Import Strategy',
                    confirmImport: 'Confirm import',
                    supportedFormats: 'Supported formats',
                    backToLibrary: 'Back',
                    strategySource: 'Strategy source',
                    importing: 'Importing',
                    validationTitle: 'Validation checks',
                    validationEntrypoint: 'Entrypoint detection',
                    validationSyntax: 'Python syntax',
                    validationReturn: 'Order list return',
                    validationMetadata: 'Metadata detection',
                    validationPass: 'Passed',
                    validationWarn: 'Needs review',
                    validationUnknown: 'Not checked',
                    sourceTemplate: 'Template',
                    sourceImport: 'Imported file',
                  },
                },
                strategyNew: {
                  nameLabel: 'Strategy name',
                  symbolLabel: 'Primary symbol',
                },
                marketplace: {
                  category: 'Category',
                  tags: 'Tags',
                },
              },
            },
          }),
        ],
      },
    })
  }

  it('renders readable validation states and redirects into guided next steps after confirm', async () => {
    confirmStrategyImportMock.mockResolvedValue({
      strategy: {
        id: 'strategy-1',
        name: 'Double Moving Average',
      },
      next: '/strategies/strategy-1/parameters',
    })

    const wrapper = mountView()
    expect(wrapper.get('[data-test="validation-entrypoint"]').text()).toContain('Passed')
    expect(wrapper.get('[data-test="validation-syntax"]').text()).toContain('Passed')
    expect(wrapper.get('[data-test="validation-return"]').text()).toContain('Passed')

    await wrapper.get('[data-test="confirm-import"]').trigger('click')
    await flushPromises()

    expect(pushMock).toHaveBeenCalledWith({
      path: '/strategies/strategy-1/parameters',
      query: {
        guided: 'true',
        source: 'template',
      },
    })
  })
})
