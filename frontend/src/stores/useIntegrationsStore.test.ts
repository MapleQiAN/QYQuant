import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const {
  fetchIntegrationProvidersMock,
  fetchIntegrationsMock,
  createIntegrationMock,
  validateIntegrationMock,
  fetchIntegrationAccountMock,
  fetchIntegrationPositionsMock,
  toastSuccessMock,
  toastWarningMock,
} = vi.hoisted(() => ({
  fetchIntegrationProvidersMock: vi.fn(),
  fetchIntegrationsMock: vi.fn(),
  createIntegrationMock: vi.fn(),
  validateIntegrationMock: vi.fn(),
  fetchIntegrationAccountMock: vi.fn(),
  fetchIntegrationPositionsMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastWarningMock: vi.fn(),
}))

vi.mock('../api/integrations', () => ({
  fetchIntegrationProviders: fetchIntegrationProvidersMock,
  fetchIntegrations: fetchIntegrationsMock,
  createIntegration: createIntegrationMock,
  validateIntegration: validateIntegrationMock,
  fetchIntegrationAccount: fetchIntegrationAccountMock,
  fetchIntegrationPositions: fetchIntegrationPositionsMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    warning: toastWarningMock,
  }
}))

import { useIntegrationsStore } from './useIntegrationsStore'

describe('integrations store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchIntegrationProvidersMock.mockReset()
    fetchIntegrationsMock.mockReset()
    createIntegrationMock.mockReset()
    validateIntegrationMock.mockReset()
    fetchIntegrationAccountMock.mockReset()
    fetchIntegrationPositionsMock.mockReset()
    toastSuccessMock.mockReset()
    toastWarningMock.mockReset()
  })

  it('loads provider catalog and integrations', async () => {
    fetchIntegrationProvidersMock.mockResolvedValueOnce([
      { key: 'joinquant', name: 'JoinQuant', type: 'market_data', mode: 'hosted', capabilities: {}, configSchema: {}, isEnabled: true }
    ])
    fetchIntegrationsMock.mockResolvedValueOnce([
      {
        id: 'integration-1',
        providerKey: 'longport',
        displayName: 'Main Account',
        status: 'active',
        configPublic: { region: 'hk' },
        lastValidatedAt: null,
        lastSuccessAt: null,
        lastFailureAt: null,
        lastErrorMessage: null,
        createdAt: null,
        updatedAt: null,
      }
    ])

    const store = useIntegrationsStore()
    await store.loadProviders()
    await store.loadIntegrations()

    expect(store.providers).toHaveLength(1)
    expect(store.integrations).toHaveLength(1)
  })

  it('creates and appends a new integration', async () => {
    createIntegrationMock.mockResolvedValueOnce({
      id: 'integration-1',
      providerKey: 'longport',
      displayName: 'Main Account',
      status: 'active',
      configPublic: { region: 'hk' },
      lastValidatedAt: null,
      lastSuccessAt: null,
      lastFailureAt: null,
      lastErrorMessage: null,
      createdAt: null,
      updatedAt: null,
    })

    const store = useIntegrationsStore()
    const result = await store.createIntegration({
      providerKey: 'longport',
      displayName: 'Main Account',
      configPublic: { region: 'hk' },
      secretPayload: { access_token: 'token-1' }
    })

    expect(result.id).toBe('integration-1')
    expect(store.integrations).toHaveLength(1)
    expect(toastSuccessMock).toHaveBeenCalledWith('连接已创建')
  })

  it('validates integration and loads account and positions', async () => {
    validateIntegrationMock.mockResolvedValueOnce({ status: 'valid', message: 'ok' })
    fetchIntegrationAccountMock.mockResolvedValueOnce({ currency: 'HKD', equity: '12345.67' })
    fetchIntegrationPositionsMock.mockResolvedValueOnce([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])

    const store = useIntegrationsStore()
    const validation = await store.validateIntegration('integration-1')
    const account = await store.loadAccount('integration-1')
    const positions = await store.loadPositions('integration-1')

    expect(validation.status).toBe('valid')
    expect(account).toEqual({ currency: 'HKD', equity: '12345.67' })
    expect(positions).toEqual([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])
    expect(store.accountById['integration-1']).toEqual({ currency: 'HKD', equity: '12345.67' })
    expect(store.positionsById['integration-1']).toEqual([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])
    expect(toastSuccessMock).toHaveBeenNthCalledWith(1, '连接验证成功')
    expect(toastSuccessMock).toHaveBeenNthCalledWith(2, '账户信息已加载')
    expect(toastSuccessMock).toHaveBeenNthCalledWith(3, '持仓信息已加载')
  })
})
