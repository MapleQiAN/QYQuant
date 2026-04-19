import { createHttpClient } from './http'

const client = createHttpClient()

export interface IntegrationProvider {
  key: string
  name: string
  type: 'market_data' | 'broker_account' | 'llm'
  mode: 'hosted' | 'local_connector'
  capabilities: Record<string, boolean>
  configSchema: Record<string, unknown>
  isEnabled: boolean
}

export interface UserIntegration {
  id: string
  providerKey: string
  displayName: string
  status: string
  configPublic: Record<string, unknown>
  lastValidatedAt: string | null
  lastSuccessAt: string | null
  lastFailureAt: string | null
  lastErrorMessage: string | null
  createdAt: string | null
  updatedAt: string | null
}

export interface CreateIntegrationPayload {
  providerKey: string
  displayName: string
  configPublic: Record<string, unknown>
  secretPayload: Record<string, unknown>
}

export interface UpdateIntegrationPayload {
  displayName?: string
  configPublic?: Record<string, unknown>
  secretPayload?: Record<string, unknown>
}

interface IntegrationProviderDto {
  key: string
  name?: string | null
  type?: string | null
  mode?: string | null
  capabilities?: Record<string, boolean> | null
  config_schema?: Record<string, unknown> | null
  is_enabled?: boolean | null
}

interface UserIntegrationDto {
  id: string
  provider_key?: string | null
  display_name?: string | null
  status?: string | null
  config_public?: Record<string, unknown> | null
  last_validated_at?: string | null
  last_success_at?: string | null
  last_failure_at?: string | null
  last_error_message?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export function fetchIntegrationProviders(): Promise<IntegrationProvider[]> {
  return client.request<IntegrationProviderDto[]>({
    method: 'get',
    url: '/v1/integrations/providers'
  }).then((items) => (items ?? []).map(normalizeProvider))
}

export function fetchIntegrations(): Promise<UserIntegration[]> {
  return client.request<UserIntegrationDto[]>({
    method: 'get',
    url: '/v1/integrations'
  }).then((items) => (items ?? []).map(normalizeIntegration))
}

export function createIntegration(payload: CreateIntegrationPayload): Promise<UserIntegration> {
  return client.request<UserIntegrationDto>({
    method: 'post',
    url: '/v1/integrations',
    data: {
      provider_key: payload.providerKey,
      display_name: payload.displayName,
      config_public: payload.configPublic,
      secret_payload: payload.secretPayload
    }
  }).then(normalizeIntegration)
}

export function deleteIntegration(integrationId: string): Promise<void> {
  return client.request<void>({
    method: 'delete',
    url: `/v1/integrations/${integrationId}`
  })
}

export function updateIntegration(integrationId: string, payload: UpdateIntegrationPayload): Promise<UserIntegration> {
  return client.request<UserIntegrationDto>({
    method: 'patch',
    url: `/v1/integrations/${integrationId}`,
    data: {
      display_name: payload.displayName,
      config_public: payload.configPublic,
      secret_payload: payload.secretPayload,
    }
  }).then(normalizeIntegration)
}

export function validateIntegration(integrationId: string): Promise<{ status: string; message: string | null }> {
  return client.request<{ status?: string | null; message?: string | null }>({
    method: 'post',
    url: `/v1/integrations/${integrationId}/validate`
  }).then((data) => ({
    status: data.status ?? 'unknown',
    message: data.message ?? null
  }))
}

export function fetchIntegrationAccount(integrationId: string): Promise<Record<string, unknown>> {
  return client.request<Record<string, unknown>>({
    method: 'get',
    url: `/v1/integrations/${integrationId}/account`
  })
}

export function fetchIntegrationPositions(integrationId: string): Promise<Record<string, unknown>[]> {
  return client.request<Record<string, unknown>[]>({
    method: 'get',
    url: `/v1/integrations/${integrationId}/positions`
  })
}

function normalizeProvider(item: IntegrationProviderDto): IntegrationProvider {
  return {
    key: item.key,
    name: item.name ?? item.key,
    type:
      item.type === 'broker_account'
        ? 'broker_account'
        : item.type === 'llm'
          ? 'llm'
          : 'market_data',
    mode: item.mode === 'local_connector' ? 'local_connector' : 'hosted',
    capabilities: item.capabilities ?? {},
    configSchema: item.config_schema ?? {},
    isEnabled: item.is_enabled !== false
  }
}

function normalizeIntegration(item: UserIntegrationDto): UserIntegration {
  return {
    id: item.id,
    providerKey: item.provider_key ?? '',
    displayName: item.display_name ?? '',
    status: item.status ?? 'draft',
    configPublic: item.config_public ?? {},
    lastValidatedAt: item.last_validated_at ?? null,
    lastSuccessAt: item.last_success_at ?? null,
    lastFailureAt: item.last_failure_at ?? null,
    lastErrorMessage: item.last_error_message ?? null,
    createdAt: item.created_at ?? null,
    updatedAt: item.updated_at ?? null
  }
}
