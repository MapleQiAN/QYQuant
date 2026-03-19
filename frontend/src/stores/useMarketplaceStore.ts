import { defineStore } from 'pinia'
import {
  fetchMarketplaceStrategies,
  fetchMarketplaceStrategyDetail,
  fetchMarketplaceStrategyEquityCurve,
  fetchMarketplaceStrategyImportStatus,
  importMarketplaceStrategy
} from '../api/strategies'
import type {
  MarketplaceStrategy,
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
  MarketplaceStrategyImportResult,
  MarketplaceStrategyImportStatus
} from '../types/Strategy'

const DEFAULT_PAGE_SIZE = 20
const FEATURED_PAGE_SIZE = 6

const emptyEquityCurve: MarketplaceStrategyEquityCurve = {
  dates: [],
  values: []
}

export const useMarketplaceStore = defineStore('marketplace', {
  state: () => ({
    strategies: [] as MarketplaceStrategy[],
    featuredStrategies: [] as MarketplaceStrategy[],
    currentStrategy: null as MarketplaceStrategyDetail | null,
    equityCurve: { ...emptyEquityCurve } as MarketplaceStrategyEquityCurve,
    loading: false,
    featuredLoading: false,
    curveLoading: false,
    importLoading: false,
    importStatusLoading: false,
    featuredError: null as string | null,
    curveError: null as string | null,
    error: null as string | null,
    total: 0,
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE
  }),
  actions: {
    async fetchStrategies(page = 1) {
      this.loading = true
      this.error = null
      try {
        const result = await fetchMarketplaceStrategies({ page, pageSize: this.pageSize })
        this.strategies = result.data
        this.total = toNumber((result.meta as any).total, 0)
        this.page = toNumber((result.meta as any).page, page)
        this.pageSize = toNumber((result.meta as any).pageSize ?? (result.meta as any).page_size, this.pageSize)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load marketplace strategies'
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchFeatured() {
      this.featuredLoading = true
      this.featuredError = null
      try {
        const result = await fetchMarketplaceStrategies({ featured: true, pageSize: FEATURED_PAGE_SIZE })
        this.featuredStrategies = result.data
      } catch (error: any) {
        this.featuredError = error?.message || 'Failed to load featured strategies'
      } finally {
        this.featuredLoading = false
      }
    },
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
      this.curveError = null
      try {
        this.equityCurve = await fetchMarketplaceStrategyEquityCurve(strategyId)
      } catch (error: any) {
        this.curveError = error?.message || 'Failed to load equity curve'
      } finally {
        this.curveLoading = false
      }
    },
    async checkImportStatus(strategyId: string): Promise<MarketplaceStrategyImportStatus> {
      this.importStatusLoading = true
      try {
        const result = await fetchMarketplaceStrategyImportStatus(strategyId)
        if (this.currentStrategy?.id === strategyId) {
          this.currentStrategy = {
            ...this.currentStrategy,
            alreadyImported: result.imported,
            importedStrategyId: result.userStrategyId
          }
        }
        return result
      } catch (error: any) {
        if (error?.status === 401) {
          return { imported: false, userStrategyId: null }
        }
        this.error = error?.message || 'Failed to check marketplace import status'
        throw error
      } finally {
        this.importStatusLoading = false
      }
    },
    async importStrategy(strategyId: string): Promise<MarketplaceStrategyImportResult> {
      this.importLoading = true
      this.error = null
      try {
        const result = await importMarketplaceStrategy(strategyId)
        if (this.currentStrategy?.id === strategyId) {
          this.currentStrategy = {
            ...this.currentStrategy,
            alreadyImported: true,
            importedStrategyId: result.strategyId
          }
        }
        return result
      } catch (error: any) {
        this.error = error?.message || 'Failed to import marketplace strategy'
        throw error
      } finally {
        this.importLoading = false
      }
    },
    reset() {
      this.currentStrategy = null
      this.equityCurve = { ...emptyEquityCurve }
      this.loading = false
      this.featuredLoading = false
      this.curveLoading = false
      this.importLoading = false
      this.importStatusLoading = false
      this.featuredError = null
      this.curveError = null
      this.error = null
    }
  }
})

function toNumber(value: unknown, fallback: number): number {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return fallback
}
