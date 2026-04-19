import { defineStore } from 'pinia'
import {
  createIntegration as createIntegrationRequest,
  deleteIntegration as deleteIntegrationRequest,
  fetchIntegrationAccount,
  fetchIntegrationPositions,
  fetchIntegrationProviders,
  fetchIntegrations,
  updateIntegration as updateIntegrationRequest,
  type CreateIntegrationPayload,
  type IntegrationProvider,
  type UpdateIntegrationPayload,
  type UserIntegration,
  validateIntegration as validateIntegrationRequest,
} from '../api/integrations'
import { toast } from '../lib/toast'

const ACTIVE_AI_KEY = 'qyquant-active-ai-integration'

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
    activeAiIntegrationId: (typeof window !== 'undefined' && typeof window.localStorage?.getItem === 'function')
      ? (window.localStorage.getItem(ACTIVE_AI_KEY) || '')
      : '',
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
        toast.success('连接已创建')
        return integration
      } finally {
        this.createSubmitting = false
      }
    },
    async validateIntegration(integrationId: string) {
      const result = await validateIntegrationRequest(integrationId)
      this.validationState[integrationId] = result
      if (result.status === 'valid') {
        toast.success('连接验证成功')
      } else {
        toast.warning(result.message || '连接验证未通过')
      }
      return result
    },
    async loadAccount(integrationId: string) {
      const data = await fetchIntegrationAccount(integrationId)
      this.accountById[integrationId] = data
      toast.success('账户信息已加载')
      return data
    },
    async loadPositions(integrationId: string) {
      const data = await fetchIntegrationPositions(integrationId)
      this.positionsById[integrationId] = data
      toast.success('持仓信息已加载')
      return data
    },
    async deleteIntegration(integrationId: string) {
      await deleteIntegrationRequest(integrationId)
      this.integrations = this.integrations.filter((i) => i.id !== integrationId)
      if (this.activeAiIntegrationId === integrationId) {
        this.setActiveAiIntegration('')
      }
      toast.success('配置已删除')
    },
    async updateIntegration(integrationId: string, payload: UpdateIntegrationPayload) {
      const updated = await updateIntegrationRequest(integrationId, payload)
      this.integrations = this.integrations.map((i) => i.id === integrationId ? updated : i)
      toast.success('配置已更新')
      return updated
    },
    setActiveAiIntegration(integrationId: string) {
      this.activeAiIntegrationId = integrationId
      if (typeof window !== 'undefined' && typeof window.localStorage?.setItem === 'function') {
        if (integrationId) {
          window.localStorage.setItem(ACTIVE_AI_KEY, integrationId)
        } else {
          window.localStorage.removeItem(ACTIVE_AI_KEY)
        }
      }
    }
  }
})
