import { defineStore } from 'pinia'
import { acceptSimDisclaimer, createSimBot } from '../api/simulation'
import type { CreateBotPayload, SimulationBot } from '../types/Simulation'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    bots: [] as SimulationBot[],
    isLoading: false,
    error: null as string | null,
    errorCode: null as string | null,
  }),
  actions: {
    clearError() {
      this.error = null
      this.errorCode = null
    },
    async acceptDisclaimer() {
      await acceptSimDisclaimer()
    },
    async createBot(payload: CreateBotPayload): Promise<SimulationBot> {
      this.isLoading = true
      this.clearError()
      try {
        const bot = await createSimBot(payload)
        this.bots.unshift(bot)
        return bot
      } catch (error: any) {
        this.error = error?.message || 'Failed to create simulation bot'
        this.errorCode = error?.code || null
        throw error
      } finally {
        this.isLoading = false
      }
    },
  },
})
