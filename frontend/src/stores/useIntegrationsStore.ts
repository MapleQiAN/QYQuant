import { defineStore } from 'pinia'
import {
  createIntegration as createIntegrationRequest,
  fetchIntegrationAccount,
  fetchIntegrationPositions,
  fetchIntegrationProviders,
  fetchIntegrations,
  type CreateIntegrationPayload,
  type IntegrationProvider,
  type UserIntegration,
  validateIntegration as validateIntegrationRequest,
} from '../api/integrations'

export const useIntegrationsStore = defineStore('integrations', {
  state: () => ({
    providers: [] as IntegrationProvider[],
    integrations: [] as UserIntegration[],
    providersLoading: false,
    integrationsLoading: false,
    createSubmitting: false,
    validationState: {} as Record<string, { status: string; message: string | null }>,
    accountById: {} as Record<string, Record<string, unknown>>,
    positionsById: {} as Record<string, Record<string, unknown>[]>,
  }),
  actions: {
    async loadProviders() {
      this.providersLoading = true
      try {
        this.providers = await fetchIntegrationProviders()
      } finally {
        this.providersLoading = false
      }
    },
    async loadIntegrations() {
      this.integrationsLoading = true
      try {
        this.integrations = await fetchIntegrations()
      } finally {
        this.integrationsLoading = false
      }
    },
    async createIntegration(payload: CreateIntegrationPayload) {
      this.createSubmitting = true
      try {
        const integration = await createIntegrationRequest(payload)
        this.integrations = [integration, ...this.integrations]
        return integration
      } finally {
        this.createSubmitting = false
      }
    },
    async validateIntegration(integrationId: string) {
      const result = await validateIntegrationRequest(integrationId)
      this.validationState[integrationId] = result
      return result
    },
    async loadAccount(integrationId: string) {
      const data = await fetchIntegrationAccount(integrationId)
      this.accountById[integrationId] = data
      return data
    },
    async loadPositions(integrationId: string) {
      const data = await fetchIntegrationPositions(integrationId)
      this.positionsById[integrationId] = data
      return data
    }
  }
})
