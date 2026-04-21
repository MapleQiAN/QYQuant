<template>
  <section class="marketplace-page">
    <div class="container">
      <header class="page-header fade-in">
        <div>
          <h1 class="page-title">{{ $t('marketplace.pageTitle') }}</h1>
          <p class="page-subtitle">{{ $t('marketplace.pageSubtitle') }}</p>
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
            :placeholder="$t('marketplace.searchPlaceholder')"
          />
        </label>
        <div class="chip-row">
          <button
            type="button"
            class="filter-chip"
            :class="{ active: !hasActiveFilters }"
            @click="clearAllFilters"
          >
            {{ $t('marketplace.allCategories') }}
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
          <h2 class="section-title">{{ $t('marketplace.featuredPicks') }}</h2>
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
          <h2 class="section-title">{{ $t('marketplace.allStrategies') }}</h2>
          <span class="section-meta">{{ $t('marketplace.resultsCount', { count: store.total }) }}</span>
        </div>

        <div v-if="store.loading" class="empty-state">{{ $t('marketplace.loading') }}</div>
        <p v-else-if="store.error" class="message error">{{ store.error }}</p>
        <div
          v-else-if="store.strategies.length === 0"
          class="empty-state"
          data-test="marketplace-empty"
        >
          <p>{{ hasActiveFilters ? $t('marketplace.noMatch') : $t('marketplace.noPublic') }}</p>
          <button
            v-if="hasActiveFilters"
            data-test="marketplace-clear-filters"
            type="button"
            class="btn btn-secondary"
            @click="clearAllFilters"
          >
            {{ $t('marketplace.clearFilters') }}
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
            {{ $t('marketplace.previous') }}
          </button>
          <span>{{ $t('marketplace.pageIndicator', { current: store.page, total: totalPages }) }}</span>
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="store.page >= totalPages || store.loading"
            @click="changePage(store.page + 1)"
          >
            {{ $t('marketplace.nextPage') }}
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import FeaturedStrategyCard from '../components/strategy/FeaturedStrategyCard.vue'
import StrategyCard from '../components/strategy/StrategyCard.vue'
import { useMarketplaceStore } from '../stores'

const router = useRouter()
const store = useMarketplaceStore()
const { t } = useI18n()
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
    label: t('marketplace.filterTrendFollowing'),
    active: store.filters.category === 'trend-following',
    onClick: () => toggleCategory('trend-following')
  },
  {
    key: 'mean-reversion',
    label: t('marketplace.filterMeanReversion'),
    active: store.filters.category === 'mean-reversion',
    onClick: () => toggleCategory('mean-reversion')
  },
  {
    key: 'momentum',
    label: t('marketplace.filterMomentum'),
    active: store.filters.category === 'momentum',
    onClick: () => toggleCategory('momentum')
  },
  {
    key: 'multi-indicator',
    label: t('marketplace.filterMultiIndicator'),
    active: store.filters.category === 'multi-indicator',
    onClick: () => toggleCategory('multi-indicator')
  },
  {
    key: 'annual-return',
    label: t('marketplace.filterAnnualReturn'),
    active: store.filters.annualReturnGte === 20,
    onClick: () => toggleMetric('annualReturnGte', 20)
  },
  {
    key: 'drawdown',
    label: t('marketplace.filterDrawdown'),
    active: store.filters.maxDrawdownLte === 10,
    onClick: () => toggleMetric('maxDrawdownLte', 10)
  },
  {
    key: 'verified',
    label: t('marketplace.filterVerified'),
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
  position: relative;
  padding-bottom: var(--spacing-lg);
}

.page-header::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  height: 6px;
  background: var(--color-accent);
  border-radius: 3px;
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxxl);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-md);
}

/* ── Toolbar ── */
.toolbar-card {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.toolbar-card::before {
  content: "";
  position: absolute;
  width: 40px;
  height: 40px;
  background: var(--color-accent);
  border-radius: 50%;
  top: -12px;
  right: -12px;
  opacity: 0.9;
}

.search-shell {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  border-radius: 999px;
  border: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-shell:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.search-icon {
  color: var(--color-text-muted);
  font-size: var(--font-size-md);
  font-weight: 800;
}

.search-input {
  width: 100%;
  padding: 12px 0;
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-md);
}

.search-input:focus {
  outline: none;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  position: relative;
  z-index: 1;
}

.filter-chip {
  padding: 7px 14px;
  border-radius: 9999px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.filter-chip:hover {
  border-color: var(--color-border-hover);
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.filter-chip.active {
  background: var(--color-accent);
  border-color: var(--color-border);
  color: var(--color-text-primary);
  font-weight: 800;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* ── Section titles ── */
.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  position: relative;
  padding-left: 14px;
}

.section-title-row::before {
  content: "";
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 5px;
  background: var(--color-primary);
  border-radius: 3px;
}

.section-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: 900;
  letter-spacing: -0.01em;
}

.section-meta {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 600;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

/* ── Featured ── */
.featured-section {
  margin-bottom: var(--spacing-xl);
}

.featured-strip {
  display: flex;
  gap: var(--spacing-md);
  overflow-x: auto;
  padding-bottom: var(--spacing-xs);
}

/* ── Grid ── */
.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
}

/* ── Empty / Messages ── */
.empty-state {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-weight: 600;
}

.message.error {
  color: var(--color-danger);
  font-weight: 700;
  padding: var(--spacing-md);
  border: 2px solid var(--color-danger);
  border-radius: var(--radius-sm);
  background: var(--color-danger-bg);
}

.message.warning {
  margin-bottom: var(--spacing-md);
  color: var(--color-warning);
  font-weight: 700;
  padding: var(--spacing-md);
  border: 2px solid var(--color-warning);
  border-radius: var(--radius-sm);
  background: var(--color-warning-bg);
}

/* ── Pagination ── */
.pagination {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.pagination .btn {
  border: 2px solid var(--color-border);
  border-radius: 999px;
  padding: 8px 16px;
  font-weight: 800;
  font-size: var(--font-size-sm);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast);
}

.pagination .btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.pagination .btn:disabled {
  opacity: 0.35;
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
