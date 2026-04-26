<template>
  <article class="featured-card card">
    <header class="card-head">
      <div>
        <p class="card-kicker">{{ strategy.category || $t('marketplace.strategyDefault') }}</p>
        <h3 class="card-title">{{ strategy.title }}</h3>
      </div>
      <VerifiedBadge v-if="strategy.isVerified" />
    </header>

    <p class="card-description">{{ strategy.description || $t('marketplace.noDescription') }}</p>

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
        <span class="author-name">{{ strategy.author.nickname || $t('marketplace.unknownAuthor') }}</span>
      </div>
      <button
        type="button"
        class="btn btn-primary"
        data-test="featured-cta"
        @click="emit('open', strategy.id)"
      >
        {{ $t('marketplace.tryBacktest') }}
      </button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MarketplaceStrategy } from '../../types/Strategy'
import VerifiedBadge from './VerifiedBadge.vue'

const { t } = useI18n()

const emit = defineEmits<{
  (event: 'open', strategyId: string): void
}>()

const props = defineProps<{
  strategy: MarketplaceStrategy
}>()

const metrics = computed(() => [
  {
    label: t('marketplace.metricAnnualized'),
    value: formatMetric(props.strategy.displayMetrics.annualized_return, true)
  },
  {
    label: t('marketplace.metricDrawdown'),
    value: formatMetric(props.strategy.displayMetrics.max_drawdown, true)
  },
  {
    label: t('marketplace.metricSharpe'),
    value: formatMetric(props.strategy.displayMetrics.sharpe_ratio, false)
  }
])

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
.featured-card {
  width: min(100%, 560px);
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.featured-card::before {
  content: "";
  position: absolute;
  width: 60px;
  height: 60px;
  background: var(--color-danger);
  border-radius: 50%;
  top: -20px;
  right: -20px;
  opacity: 0.88;
}

.featured-card::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
  border-radius: 0 0 14px 14px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.card-kicker {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.card-title {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xl);
  font-weight: 900;
  letter-spacing: -0.01em;
}

.card-description {
  margin-top: var(--spacing-md);
  color: var(--color-text-secondary);
  min-height: 44px;
  position: relative;
  z-index: 1;
}

.metric-row {
  margin-top: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.metric-item {
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 2px solid #eaeaea;
}

.metric-label {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.metric-value {
  margin-top: 4px;
  font-size: var(--font-size-md);
  color: var(--color-primary);
  font-weight: 800;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.card-foot {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  border-top: 2px dashed #e0e0dc;
  padding-top: var(--spacing-md);
  position: relative;
  z-index: 1;
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
}

.author-name {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .featured-card {
    width: 100%;
  }
}
</style>
