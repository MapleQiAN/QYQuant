<template>
  <section class="marketplace-page">
    <div class="container">
      <header class="page-header">
        <div>
          <h1 class="page-title">Marketplace</h1>
          <p class="page-subtitle">Discover public strategies curated by the community and editorial picks.</p>
        </div>
      </header>

      <section class="toolbar-card">
        <label class="search-shell">
          <span class="search-icon">⌕</span>
          <input
            v-model="searchInput"
            data-test="marketplace-search-input"
            class="search-input"
            type="search"
            placeholder="Search strategy name, category, or tags"
          />
        </label>
        <div class="chip-row">
          <button
            type="button"
            class="filter-chip"
            :class="{ active: !hasActiveFilters }"
            @click="clearAllFilters"
          >
            All
          </button>
          <button
            v-for="chip in filterChips"
            :key="chip.key"
            type="button"
            class="filter-chip"
            :class="{ active: chip.active }"
            @click="chip.onClick"
          >
            {{ chip.label }}
          </button>
        </div>
      </section>

      <section
        v-if="store.featuredStrategies.length > 0"
        class="featured-section"
        data-test="featured-section"
      >
        <div class="section-title-row">
          <h2 class="section-title">Featured Picks</h2>
        </div>
        <div class="featured-strip">
          <FeaturedStrategyCard
            v-for="strategy in store.featuredStrategies"
            :key="strategy.id"
            :strategy="strategy"
            @open="openStrategyDetail"
          />
        </div>
      </section>
      <p v-else-if="store.featuredError" class="message warning" data-test="featured-error">
        {{ store.featuredError }}
      </p>

      <section class="grid-section">
        <div class="section-title-row">
          <h2 class="section-title">All Strategies</h2>
          <span class="section-meta">{{ store.total }} results</span>
        </div>

        <div v-if="store.loading" class="empty-state">Loading marketplace strategies...</div>
        <p v-else-if="store.error" class="message error">{{ store.error }}</p>
        <div
          v-else-if="store.strategies.length === 0"
          class="empty-state"
          data-test="marketplace-empty"
        >
          <p>{{ hasActiveFilters ? 'No strategies match the current search and filters.' : 'No public strategies yet.' }}</p>
          <button
            v-if="hasActiveFilters"
            data-test="marketplace-clear-filters"
            type="button"
            class="btn btn-secondary"
            @click="clearAllFilters"
          >
            Clear filters
          </button>
        </div>
        <div v-else class="strategy-grid" data-test="marketplace-grid">
          <StrategyCard
            v-for="strategy in store.strategies"
            :key="strategy.id"
            :strategy="strategy"
            @open="openStrategyDetail"
          />
        </div>

        <div class="pagination" data-test="marketplace-pagination">
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="store.page <= 1 || store.loading"
            @click="changePage(store.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ store.page }} / {{ totalPages }}</span>
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="store.page >= totalPages || store.loading"
            @click="changePage(store.page + 1)"
          >
            Next
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import FeaturedStrategyCard from '../components/strategy/FeaturedStrategyCard.vue'
import StrategyCard from '../components/strategy/StrategyCard.vue'
import { useMarketplaceStore } from '../stores'

const router = useRouter()
const store = useMarketplaceStore()
const searchInput = ref(store.filters.q)
let searchTimer: number | undefined

const totalPages = computed(() => Math.max(1, Math.ceil(store.total / Math.max(store.pageSize, 1))))
const hasActiveFilters = computed(
  () =>
    Boolean(store.filters.q) ||
    Boolean(store.filters.category) ||
    store.filters.verified ||
    store.filters.annualReturnGte !== null ||
    store.filters.maxDrawdownLte !== null
)

const filterChips = computed(() => [
  {
    key: 'trend-following',
    label: 'Trend Following',
    active: store.filters.category === 'trend-following',
    onClick: () => toggleCategory('trend-following')
  },
  {
    key: 'mean-reversion',
    label: 'Mean Reversion',
    active: store.filters.category === 'mean-reversion',
    onClick: () => toggleCategory('mean-reversion')
  },
  {
    key: 'momentum',
    label: 'Momentum',
    active: store.filters.category === 'momentum',
    onClick: () => toggleCategory('momentum')
  },
  {
    key: 'multi-indicator',
    label: 'Multi Indicator',
    active: store.filters.category === 'multi-indicator',
    onClick: () => toggleCategory('multi-indicator')
  },
  {
    key: 'annual-return',
    label: 'Annual > 20%',
    active: store.filters.annualReturnGte === 20,
    onClick: () => toggleMetric('annualReturnGte', 20)
  },
  {
    key: 'drawdown',
    label: 'Drawdown < 10%',
    active: store.filters.maxDrawdownLte === 10,
    onClick: () => toggleMetric('maxDrawdownLte', 10)
  },
  {
    key: 'verified',
    label: 'Platform Verified',
    active: store.filters.verified,
    onClick: () => toggleVerified()
  }
])

onMounted(() => {
  void store.fetchFeatured()
  void store.fetchStrategies(1)
})

onBeforeUnmount(() => {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
})

watch(searchInput, (value) => {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(() => {
    store.setFilter('q', value.trim())
    void store.fetchStrategies(1)
  }, 300)
})

function changePage(nextPage: number) {
  if (nextPage < 1 || nextPage > totalPages.value) {
    return
  }
  void store.fetchStrategies(nextPage)
}

function toggleCategory(category: string) {
  store.setFilter('category', store.filters.category === category ? null : category)
  void store.fetchStrategies(1)
}

function toggleMetric(key: 'annualReturnGte' | 'maxDrawdownLte', value: number) {
  store.setFilter(key, store.filters[key] === value ? null : value)
  void store.fetchStrategies(1)
}

function toggleVerified() {
  store.setFilter('verified', !store.filters.verified)
  void store.fetchStrategies(1)
}

function clearAllFilters() {
  searchInput.value = ''
  store.clearFilters()
  void store.fetchStrategies(1)
}

function openStrategyDetail(strategyId: string) {
  void router.push({
    name: 'marketplace-strategy-detail',
    params: { strategyId }
  })
}
</script>

<style scoped>
.marketplace-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.toolbar-card {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.search-shell {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.search-icon {
  color: var(--color-text-muted);
  font-size: var(--font-size-md);
}

.search-input {
  width: 100%;
  padding: 14px 0;
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
}

.search-input:focus {
  outline: none;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.filter-chip {
  padding: 8px 14px;
  border-radius: 9999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 12px;
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
}

.filter-chip.active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text-primary);
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.section-title {
  margin: 0;
  font-size: var(--font-size-lg);
}

.section-meta {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.featured-section {
  margin-bottom: var(--spacing-xl);
}

.featured-strip {
  display: flex;
  gap: var(--spacing-md);
  overflow-x: auto;
  padding-bottom: var(--spacing-xs);
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.empty-state {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.message.error {
  color: var(--color-danger);
}

.message.warning {
  margin-bottom: var(--spacing-md);
  color: var(--color-warning);
}

.pagination {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

@media (max-width: 1024px) {
  .strategy-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .toolbar-card {
    padding: var(--spacing-md);
  }

  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    flex-direction: column;
  }
}
</style>
