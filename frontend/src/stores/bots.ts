import { defineStore } from 'pinia'
import { createBot, fetchBotPerformance, fetchBotPositions, fetchBots, fetchRecent, updateBotStatus } from '../api/bots'
import { toast } from '../lib/toast'
import type { Bot, BotPerformance, BotPosition, BotStatus, CreateManagedBotPayload, ManagedBot } from '../types/Bot'

export const useBotsStore = defineStore('bots', {
  state: () => ({
    recent: [] as Bot[],
    items: [] as ManagedBot[],
    loading: false,
    isLoading: false,
    creating: false,
    error: null as string | null,
    positionsById: {} as Record<string, BotPosition[]>,
    performanceById: {} as Record<string, BotPerformance>,
  }),
  actions: {
    async loadRecent() {
      this.loading = true
      this.error = null
      try {
        this.recent = await fetchRecent()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load bots'
      } finally {
        this.loading = false
      }
    },
    async loadBots() {
      this.isLoading = true
      this.error = null
      try {
        this.items = await fetchBots()
      } catch (error: any) {
        this.error = error?.message || 'Failed to load managed bots'
      } finally {
        this.isLoading = false
      }
    },
    async createBot(payload: CreateManagedBotPayload) {
      this.creating = true
      this.error = null
      try {
        const bot = await createBot(payload)
        this.items.unshift(bot)
        this.recent.unshift(toRecentBot(bot))
        toast.success('托管机器人已创建')
        return bot
      } catch (error: any) {
        this.error = error?.message || 'Failed to create managed bot'
        throw error
      } finally {
        this.creating = false
      }
    },
    async pauseBot(botId: string) {
      await this.setBotStatus(botId, 'paused')
      toast.success('托管机器人已暂停')
    },
    async resumeBot(botId: string) {
      await this.setBotStatus(botId, 'active')
      toast.success('托管机器人已恢复')
    },
    async loadPositions(botId: string) {
      const positions = await fetchBotPositions(botId)
      this.positionsById[botId] = positions
      return positions
    },
    async loadPerformance(botId: string) {
      const performance = await fetchBotPerformance(botId)
      this.performanceById[botId] = performance

      const bot = this.items.find((item) => item.id === botId)
      if (bot) {
        bot.profit = performance.summary.totalProfit
        bot.totalReturnRate = performance.summary.totalReturnRate
      }
      const recent = this.recent.find((item) => item.id === botId)
      if (recent) {
        recent.profit = performance.summary.totalProfit
      }

      return performance
    },
    async setBotStatus(botId: string, status: Extract<BotStatus, 'active' | 'paused'>) {
      const result = await updateBotStatus(botId, status)
      const nextStatus = result.status

      const managed = this.items.find((item) => item.id === botId)
      if (managed) {
        managed.status = nextStatus
      }
      const recent = this.recent.find((item) => item.id === botId)
      if (recent) {
        recent.status = nextStatus
      }
    },
  },
})

function toRecentBot(bot: ManagedBot): Bot {
  return {
    id: bot.id,
    name: bot.name,
    strategy: bot.strategy,
    status: bot.status,
    profit: bot.profit,
    runtime: bot.runtime,
    capital: bot.capital,
    tags: bot.tags,
  }
}
