<template>
  <article class="featured-card card">
    <header class="card-head">
      <div>
        <p class="card-kicker">{{ strategy.category || 'strategy' }}</p>
        <h3 class="card-title">{{ strategy.title }}</h3>
      </div>
      <VerifiedBadge v-if="strategy.isVerified" />
    </header>

    <p class="card-description">{{ strategy.description || 'No description provided.' }}</p>

    <div class="metric-row">
      <div v-for="metric in metrics" :key="metric.label" class="metric-item">
        <span class="metric-label">{{ metric.label }}</span>
        <strong class="metric-value">{{ metric.value }}</strong>
      </div>
    </div>

    <footer class="card-foot">
      <div class="author">
        <img
          v-if="strategy.author.avatarUrl"
          :src="strategy.author.avatarUrl"
          :alt="strategy.author.nickname"
          class="author-avatar"
        />
        <span class="author-name">{{ strategy.author.nickname || 'Unknown author' }}</span>
      </div>
      <button type="button" class="btn btn-primary" data-test="featured-cta">Try backtest</button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MarketplaceStrategy } from '../../types/Strategy'
import VerifiedBadge from './VerifiedBadge.vue'

const props = defineProps<{
  strategy: MarketplaceStrategy
}>()

const metrics = computed(() => [
  {
    label: 'Annualized',
    value: formatMetric(props.strategy.displayMetrics.annualized_return, true)
  },
  {
    label: 'Drawdown',
    value: formatMetric(props.strategy.displayMetrics.max_drawdown, true)
  },
  {
    label: 'Sharpe',
    value: formatMetric(props.strategy.displayMetrics.sharpe_ratio, false)
  }
])

function formatMetric(value: string | number | null | undefined, percent: boolean) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return percent ? `${value.toFixed(2)}%` : value.toFixed(2)
  }
  if (typeof value === 'string' && value.length > 0) {
    return percent ? `${value}%` : value
  }
  return '--'
}
</script>

<style scoped>
.featured-card {
  width: min(100%, 560px);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.card-kicker {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
}

.card-title {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xl);
}

.card-description {
  margin-top: var(--spacing-md);
  color: var(--color-text-secondary);
  min-height: 44px;
}

.metric-row {
  margin-top: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.metric-item {
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  background: var(--color-background);
}

.metric-label {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.metric-value {
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
}

.card-foot {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.author {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
}

.author-name {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .featured-card {
    width: 100%;
  }
}
</style>
