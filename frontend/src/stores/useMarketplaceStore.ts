import { defineStore } from 'pinia'
import {
  fetchMarketplaceStrategies,
  fetchMarketplaceStrategyDetail,
  fetchMarketplaceStrategyPosts,
  fetchMarketplaceStrategyEquityCurve,
  fetchMarketplaceStrategyImportStatus,
  fetchMarketplacePublishStatus,
  launchMarketplaceTrialBacktest,
  importMarketplaceStrategy,
  reportMarketplaceStrategy,
  publishMarketplaceStrategy
} from '../api/strategies'
import type { CommunityPost } from '../types/community'
import type {
  MarketplaceFilters,
  MarketplacePublishPayload,
  MarketplacePublishResult,
  MarketplacePublishStatus,
  MarketplaceStrategy,
  MarketplaceStrategyDetail,
  MarketplaceStrategyEquityCurve,
  MarketplaceStrategyImportResult,
  MarketplaceStrategyReportResult,
  MarketplaceStrategyImportStatus,
  MarketplaceTrialBacktestPayload,
  MarketplaceTrialBacktestResult
} from '../types/Strategy'

const DEFAULT_PAGE_SIZE = 20
const FEATURED_PAGE_SIZE = 6

const emptyEquityCurve: MarketplaceStrategyEquityCurve = {
  dates: [],
  values: []
}

const defaultFilters = (): MarketplaceFilters => ({
  q: '',
  category: null,
  verified: false,
  annualReturnGte: null,
  maxDrawdownLte: null
})

export const useMarketplaceStore = defineStore('marketplace', {
  state: () => ({
    strategies: [] as MarketplaceStrategy[],
    featuredStrategies: [] as MarketplaceStrategy[],
    currentStrategy: null as MarketplaceStrategyDetail | null,
    relatedPostsByStrategyId: {} as Record<string, CommunityPost[]>,
    equityCurve: { ...emptyEquityCurve } as MarketplaceStrategyEquityCurve,
    loading: false,
    featuredLoading: false,
    curveLoading: false,
    importLoading: false,
    trialBacktestLoading: false,
    reportLoading: false,
    importStatusLoading: false,
    featuredError: null as string | null,
    curveError: null as string | null,
    error: null as string | null,
    filters: defaultFilters() as MarketplaceFilters,
    total: 0,
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE
  }),
  actions: {
    async fetchStrategies(page = 1) {
      this.loading = true
      this.error = null
      try {
        const result = await fetchMarketplaceStrategies({
          page,
          pageSize: this.pageSize,
          q: this.filters.q || undefined,
          category: this.filters.category,
          verified: this.filters.verified,
          annualReturnGte: this.filters.annualReturnGte,
          maxDrawdownLte: this.filters.maxDrawdownLte
        })
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
    async fetchStrategyPosts(strategyId: string) {
      this.error = null
      try {
        const response = await fetchMarketplaceStrategyPosts(strategyId)
        this.relatedPostsByStrategyId[strategyId] = response.items
        return response
      } catch (error: any) {
        this.error = error?.message || 'Failed to load related marketplace posts'
        throw error
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
    async launchTrialBacktest(
      strategyId: string,
      payload: MarketplaceTrialBacktestPayload
    ): Promise<MarketplaceTrialBacktestResult> {
      this.trialBacktestLoading = true
      this.error = null
      try {
        return await launchMarketplaceTrialBacktest(strategyId, payload)
      } catch (error: any) {
        this.error = error?.message || 'Failed to launch marketplace trial backtest'
        throw error
      } finally {
        this.trialBacktestLoading = false
      }
    },
    async reportStrategy(strategyId: string, reason: string): Promise<MarketplaceStrategyReportResult> {
      this.reportLoading = true
      this.error = null
      try {
        return await reportMarketplaceStrategy(strategyId, reason)
      } catch (error: any) {
        this.error = error?.message || 'Failed to report marketplace strategy'
        throw error
      } finally {
        this.reportLoading = false
      }
    },
    setFilter<Key extends keyof MarketplaceFilters>(key: Key, value: MarketplaceFilters[Key]) {
      this.filters[key] = value
    },
    clearFilters() {
      this.filters = defaultFilters()
    },
    async publishStrategy(payload: MarketplacePublishPayload): Promise<MarketplacePublishResult> {
      this.loading = true
      this.error = null
      try {
        return await publishMarketplaceStrategy(payload)
      } catch (error: any) {
        this.error = error?.message || 'Failed to publish strategy'
        throw error
      } finally {
        this.loading = false
      }
    },
    async getPublishStatus(strategyId: string): Promise<MarketplacePublishStatus> {
      this.loading = true
      this.error = null
      try {
        return await fetchMarketplacePublishStatus(strategyId)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load publish status'
        throw error
      } finally {
        this.loading = false
      }
    },
    reset() {
      this.currentStrategy = null
      this.relatedPostsByStrategyId = {}
      this.equityCurve = { ...emptyEquityCurve }
      this.loading = false
      this.featuredLoading = false
      this.curveLoading = false
      this.importLoading = false
      this.trialBacktestLoading = false
      this.reportLoading = false
      this.importStatusLoading = false
      this.featuredError = null
      this.curveError = null
      this.error = null
      this.filters = defaultFilters()
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
