import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SettingsView from './SettingsView.vue'
import { useUserStore } from '../stores/user'

const {
  fetchIntegrationProvidersMock,
  fetchIntegrationsMock,
  createIntegrationMock,
  validateIntegrationMock,
  fetchIntegrationAccountMock,
  fetchIntegrationPositionsMock,
} = vi.hoisted(() => ({
  fetchIntegrationProvidersMock: vi.fn(),
  fetchIntegrationsMock: vi.fn(),
  createIntegrationMock: vi.fn(),
  validateIntegrationMock: vi.fn(),
  fetchIntegrationAccountMock: vi.fn(),
  fetchIntegrationPositionsMock: vi.fn(),
}))

vi.mock('../api/integrations', () => ({
  fetchIntegrationProviders: fetchIntegrationProvidersMock,
  fetchIntegrations: fetchIntegrationsMock,
  createIntegration: createIntegrationMock,
  validateIntegration: validateIntegrationMock,
  fetchIntegrationAccount: fetchIntegrationAccountMock,
  fetchIntegrationPositions: fetchIntegrationPositionsMock,
}))

function buildI18n() {
  return createI18n({
    legacy: false,
    globalInjection: true,
    locale: 'en',
    messages: {
      en: {
        settings: {
          title: 'Settings',
          language: 'Language',
          languageHint: 'Choose your interface language.',
          zh: '中文',
          en: 'EN',
          marketStyle: 'Market Color Style',
          marketStyleHint: 'Choose how price moves are colored.',
          marketStyleCn: 'A-share style',
          marketStyleUs: 'US style',
          integrationsTitle: 'Integrations',
          integrationsHint: 'Connect broker APIs and market data providers.',
          providerLabel: 'Provider',
          displayNameLabel: 'Display name',
          connectAction: 'Connect',
          validateAction: 'Validate',
          loadAccountAction: 'Load account',
          loadPositionsAction: 'Load positions',
          emptyIntegrations: 'No integrations yet.'
        }
      },
      zh: {
        settings: {
          title: '设置',
          language: '语言',
          languageHint: '选择界面语言。',
          zh: '中文',
          en: 'EN',
          marketStyle: '行情颜色风格',
          marketStyleHint: '选择涨跌颜色显示方式。',
          marketStyleCn: 'A股风格',
          marketStyleUs: '美股风格',
          integrationsTitle: '数据源与券商连接',
          integrationsHint: '连接你的券商 API 和市场数据源。',
          providerLabel: 'Provider',
          displayNameLabel: 'Display name',
          connectAction: 'Connect',
          validateAction: 'Validate',
          loadAccountAction: 'Load account',
          loadPositionsAction: 'Load positions',
          emptyIntegrations: 'No integrations yet.'
        }
      }
    }
  })
}

describe('SettingsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchIntegrationProvidersMock.mockReset()
    fetchIntegrationsMock.mockReset()
    createIntegrationMock.mockReset()
    validateIntegrationMock.mockReset()
    fetchIntegrationAccountMock.mockReset()
    fetchIntegrationPositionsMock.mockReset()

    fetchIntegrationProvidersMock.mockResolvedValue([
      {
        key: 'longport',
        name: 'LongPort',
        type: 'broker_account',
        mode: 'hosted',
        capabilities: { positions: true },
        configSchema: {
          public_fields: ['region'],
          secret_fields: ['access_token']
        },
        isEnabled: true
      }
    ])
    fetchIntegrationsMock.mockResolvedValue([
      {
        id: 'integration-1',
        providerKey: 'longport',
        displayName: 'Main Account',
        status: 'active',
        configPublic: {},
        lastValidatedAt: null,
        lastSuccessAt: null,
        lastFailureAt: null,
        lastErrorMessage: null,
        createdAt: null,
        updatedAt: null
      }
    ])
    validateIntegrationMock.mockResolvedValue({ status: 'valid', message: 'ok' })
    fetchIntegrationAccountMock.mockResolvedValue({ currency: 'HKD', equity: '12345.67' })
    fetchIntegrationPositionsMock.mockResolvedValue([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])
  })

  it('toggles locale via store and loads integrations on mount', async () => {
    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    const store = useUserStore()
    expect(store.locale).toBeDefined()
    expect(fetchIntegrationProvidersMock).toHaveBeenCalledTimes(1)
    expect(fetchIntegrationsMock).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-locale="zh"]').trigger('click')
    expect(store.locale).toBe('zh')
  })

  it('creates and manages integrations from settings', async () => {
    createIntegrationMock.mockResolvedValueOnce({
      id: 'integration-2',
      providerKey: 'longport',
      displayName: 'New Account',
      status: 'active',
      configPublic: {},
      lastValidatedAt: null,
      lastSuccessAt: null,
      lastFailureAt: null,
      lastErrorMessage: null,
      createdAt: null,
      updatedAt: null
    })

    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    await wrapper.find('[data-provider-key="longport"]').setValue('longport')
    await wrapper.find('[data-display-name="integration-display-name"]').setValue('New Account')
    await wrapper.find('[data-public-field="region"]').setValue('hk')
    await wrapper.find('[data-secret-field="access_token"]').setValue('token-1')
    await wrapper.find('[data-action="connect-integration"]').trigger('submit')

    expect(createIntegrationMock).toHaveBeenCalledWith({
      providerKey: 'longport',
      displayName: 'New Account',
      configPublic: { region: 'hk' },
      secretPayload: { access_token: 'token-1' }
    })

    await wrapper.find('[data-action="validate-integration-integration-1"]').trigger('click')
    await wrapper.find('[data-action="load-account-integration-1"]').trigger('click')
    await wrapper.find('[data-action="load-positions-integration-1"]').trigger('click')

    expect(validateIntegrationMock).toHaveBeenCalledWith('integration-1')
    expect(fetchIntegrationAccountMock).toHaveBeenCalledWith('integration-1')
    expect(fetchIntegrationPositionsMock).toHaveBeenCalledWith('integration-1')
  })
})
