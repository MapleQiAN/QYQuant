import { defineStore } from 'pinia'
import {
  fetchMarketplaceStrategyDetail,
  fetchMarketplaceStrategyEquityCurve,
} from '../api/strategies'
import type {
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
} from '../types/Strategy'

const emptyEquityCurve: MarketplaceStrategyEquityCurve = {
  dates: [],
  values: [],
}

export const useMarketplaceStore = defineStore('marketplace', {
  state: () => ({
    currentStrategy: null as MarketplaceStrategyDetail | null,
    equityCurve: { ...emptyEquityCurve } as MarketplaceStrategyEquityCurve,
    loading: false,
    curveLoading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchStrategyDetail(strategyId: string) {
      this.loading = true
      this.error = null
      try {
        this.currentStrategy = await fetchMarketplaceStrategyDetail(strategyId)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load marketplace strategy'
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchEquityCurve(strategyId: string) {
      this.curveLoading = true
      this.error = null
      try {
        this.equityCurve = await fetchMarketplaceStrategyEquityCurve(strategyId)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load equity curve'
        throw error
      } finally {
        this.curveLoading = false
      }
    },
    reset() {
      this.currentStrategy = null
      this.equityCurve = { ...emptyEquityCurve }
      this.loading = false
      this.curveLoading = false
      this.error = null
    },
  },
})
