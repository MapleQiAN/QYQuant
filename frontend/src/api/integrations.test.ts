import { beforeEach, describe, expect, it, vi } from 'vitest'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn()
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({
    request: requestMock,
    requestWithMeta: requestMock
  })
}))

import {
  createIntegration,
  fetchIntegrationProviders,
  fetchIntegrations,
  fetchIntegrationAccount,
  fetchIntegrationPositions,
  validateIntegration,
} from './integrations'

describe('integrations api', () => {
  beforeEach(() => {
    requestMock.mockReset()
  })

  it('loads provider catalog', async () => {
    requestMock.mockResolvedValueOnce([
      { key: 'joinquant', name: 'JoinQuant', type: 'market_data', mode: 'hosted', capabilities: {}, config_schema: {}, is_enabled: true }
    ])

    const data = await fetchIntegrationProviders()

    expect(data[0]?.key).toBe('joinquant')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'get',
      url: '/v1/integrations/providers'
    })
  })

  it('creates an integration', async () => {
    requestMock.mockResolvedValueOnce({
      id: 'integration-1',
      provider_key: 'longport',
      display_name: 'Main Account',
      status: 'active',
      config_public: { region: 'hk' },
      last_validated_at: null,
      last_success_at: null,
      last_failure_at: null,
      last_error_message: null,
      created_at: null,
      updated_at: null,
    })

    const data = await createIntegration({
      providerKey: 'longport',
      displayName: 'Main Account',
      configPublic: { region: 'hk' },
      secretPayload: { access_token: 'token-1' }
    })

    expect(data.providerKey).toBe('longport')
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/integrations',
      data: {
        provider_key: 'longport',
        display_name: 'Main Account',
        config_public: { region: 'hk' },
        secret_payload: { access_token: 'token-1' }
      }
    })
  })

  it('loads integrations, validates, and fetches broker data', async () => {
    requestMock
      .mockResolvedValueOnce([
        {
          id: 'integration-1',
          provider_key: 'longport',
          display_name: 'Main Account',
          status: 'active',
          config_public: { region: 'hk' },
          last_validated_at: '2026-03-30T11:00:00+08:00',
          last_success_at: '2026-03-30T11:00:00+08:00',
          last_failure_at: null,
          last_error_message: null,
          created_at: null,
          updated_at: null,
        }
      ])
      .mockResolvedValueOnce({ status: 'valid', message: 'ok' })
      .mockResolvedValueOnce({ currency: 'HKD', equity: '12345.67' })
      .mockResolvedValueOnce([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])

    const integrations = await fetchIntegrations()
    const validation = await validateIntegration('integration-1')
    const account = await fetchIntegrationAccount('integration-1')
    const positions = await fetchIntegrationPositions('integration-1')

    expect(integrations[0]?.id).toBe('integration-1')
    expect(validation).toEqual({ status: 'valid', message: 'ok' })
    expect(account).toEqual({ currency: 'HKD', equity: '12345.67' })
    expect(positions).toEqual([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])
  })
})
