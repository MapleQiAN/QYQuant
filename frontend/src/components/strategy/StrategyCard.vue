<template>
  <article class="strategy-card card">
    <header class="card-head">
      <h3 class="card-title">{{ strategy.title }}</h3>
      <VerifiedBadge v-if="strategy.isVerified" />
    </header>

    <p class="card-description">{{ strategy.description || 'No description provided.' }}</p>
    <p class="card-category">Category: {{ strategy.category || 'other' }}</p>

    <div class="tag-row">
      <span v-for="tag in strategy.tags" :key="tag" class="chip">{{ tag }}</span>
    </div>

    <dl class="metric-grid">
      <div class="metric-cell">
        <dt>Annualized</dt>
        <dd>{{ formatMetric(strategy.displayMetrics.annualized_return, true) }}</dd>
      </div>
      <div class="metric-cell">
        <dt>Drawdown</dt>
        <dd>{{ formatMetric(strategy.displayMetrics.max_drawdown, true) }}</dd>
      </div>
      <div class="metric-cell">
        <dt>Sharpe</dt>
        <dd>{{ formatMetric(strategy.displayMetrics.sharpe_ratio, false) }}</dd>
      </div>
    </dl>

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
      <button type="button" class="btn btn-secondary" data-test="strategy-cta">Try backtest</button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import type { MarketplaceStrategy } from '../../types/Strategy'
import VerifiedBadge from './VerifiedBadge.vue'

defineProps<{
  strategy: MarketplaceStrategy
}>()

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
.strategy-card {
  padding: var(--spacing-md);
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.card-title {
  font-size: var(--font-size-lg);
  margin: 0;
}

.card-description {
  margin-top: var(--spacing-sm);
  color: var(--color-text-secondary);
  min-height: 42px;
}

.card-category {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.tag-row {
  margin-top: var(--spacing-sm);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.metric-grid {
  margin-top: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-xs);
}

.metric-cell {
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  background: var(--color-background);
}

.metric-cell dt {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.metric-cell dd {
  margin-top: 2px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.card-foot {
  margin-top: var(--spacing-md);
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
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
}

.author-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
