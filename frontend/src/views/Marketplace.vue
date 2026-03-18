<template>
  <section class="marketplace-page">
    <div class="container">
      <header class="page-header">
        <div>
          <h1 class="page-title">Marketplace</h1>
          <p class="page-subtitle">Discover public strategies curated by the community and editorial picks.</p>
        </div>
      </header>

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
          />
        </div>
      </section>
      <p v-else-if="store.featuredError" class="message warning" data-test="featured-error">
        {{ store.featuredError }}
      </p>

      <section class="grid-section">
        <div class="section-title-row">
          <h2 class="section-title">All Strategies</h2>
          <span class="section-meta">{{ store.total }} total</span>
        </div>

        <div v-if="store.loading" class="empty-state">Loading marketplace strategies...</div>
        <p v-else-if="store.error" class="message error">{{ store.error }}</p>
        <div
          v-else-if="store.strategies.length === 0"
          class="empty-state"
          data-test="marketplace-empty"
        >
          No public strategies yet.
        </div>
        <div v-else class="strategy-grid" data-test="marketplace-grid">
          <StrategyCard
            v-for="strategy in store.strategies"
            :key="strategy.id"
            :strategy="strategy"
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
import { computed, onMounted } from 'vue'
import FeaturedStrategyCard from '../components/strategy/FeaturedStrategyCard.vue'
import StrategyCard from '../components/strategy/StrategyCard.vue'
import { useMarketplaceStore } from '../stores'

const store = useMarketplaceStore()
const totalPages = computed(() => Math.max(1, Math.ceil(store.total / Math.max(store.pageSize, 1))))

onMounted(() => {
  void store.fetchFeatured()
  void store.fetchStrategies(1)
})

function changePage(nextPage: number) {
  if (nextPage < 1 || nextPage > totalPages.value) {
    return
  }
  void store.fetchStrategies(nextPage)
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

  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    flex-direction: column;
  }
}
</style>
