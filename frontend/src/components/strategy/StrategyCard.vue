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
      <button
        type="button"
        class="btn btn-secondary"
        data-test="strategy-cta"
        @click="emit('open', props.strategy.id)"
      >
        Try backtest
      </button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import type { MarketplaceStrategy } from '../../types/Strategy'
import VerifiedBadge from './VerifiedBadge.vue'

const emit = defineEmits<{
  (event: 'open', strategyId: string): void
}>()

const props = defineProps<{
  strategy: MarketplaceStrategy
}>()

function formatMetric(value: string | number | boolean | null | undefined, percent: boolean) {
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
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  transition: all var(--transition-normal);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.strategy-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
}

.strategy-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary-border);
  box-shadow: 0 12px 32px rgba(30, 90, 168, 0.15);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  margin: 0;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.card-description {
  margin-top: var(--spacing-md);
  color: var(--color-text-secondary);
  min-height: 42px;
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.card-category {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.tag-row {
  margin-top: var(--spacing-md);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.metric-grid {
  margin-top: var(--spacing-lg);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.metric-cell {
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--color-surface-elevated), var(--color-surface-active));
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.metric-cell:hover {
  border-color: var(--color-primary-border);
  background: linear-gradient(135deg, var(--color-surface-elevated), var(--color-surface-hover));
}

.metric-cell dt {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.metric-cell dd {
  margin-top: 4px;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.card-foot {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
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
  border: 2px solid var(--color-border);
  flex-shrink: 0;
}

.author-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}
</style>
