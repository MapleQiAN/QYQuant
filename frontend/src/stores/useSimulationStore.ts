import { defineStore } from 'pinia'
import { acceptSimDisclaimer, createSimBot, deleteSimBot, getSimBots, getSimPositions, patchSimBot } from '../api/simulation'
import type { CreateBotPayload, SimulationBot, SimulationPosition } from '../types/Simulation'

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
    async fetchBots(): Promise<void> {
      this.isLoading = true
      this.error = null
      try {
        this.bots = await getSimBots()
      } catch (e: any) {
        this.error = e?.message ?? '加载机器人列表失败'
      } finally {
        this.isLoading = false
      }
    },
    async fetchPositions(botId: string): Promise<SimulationPosition[]> {
      return getSimPositions(botId)
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
    async pauseBot(botId: string): Promise<void> {
      await patchSimBot(botId, { status: 'paused' })
      const bot = this.bots.find(b => b.id === botId)
      if (bot) bot.status = 'paused'
    },
    async resumeBot(botId: string): Promise<void> {
      await patchSimBot(botId, { status: 'active' })
      const bot = this.bots.find(b => b.id === botId)
      if (bot) bot.status = 'active'
    },
    async deleteBot(botId: string): Promise<void> {
      await deleteSimBot(botId)
      this.bots = this.bots.filter(b => b.id !== botId)
    },
  },
})
