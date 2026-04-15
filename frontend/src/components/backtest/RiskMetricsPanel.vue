<template>
  <section class="risk-panel">
    <div class="risk-panel__header">
      <h3 class="risk-panel__title">{{ $t('backtestReport.riskMetricsTitle') }}</h3>
      <p class="risk-panel__subtitle">{{ $t('backtestReport.riskMetricsSubtitle') }}</p>
    </div>

    <div class="risk-grid">
      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.profitFactor') }}</span>
        <strong class="risk-tile__value mono">{{ metrics.profitFactor }}</strong>
      </article>

      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.expectancy') }}</span>
        <strong :class="['risk-tile__value', 'mono', toneFromValue(metrics.expectancy)]">
          {{ metrics.expectancy }}
        </strong>
      </article>

      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.maxConsecutiveWins') }}</span>
        <strong class="risk-tile__value mono">{{ metrics.maxConsecutiveWins }}</strong>
      </article>

      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.valueAtRisk95') }}</span>
        <strong class="risk-tile__value mono">{{ metrics.valueAtRisk95 }}</strong>
        <span v-if="metrics.varDisclaimer" class="risk-tile__disclaimer">
          {{ $t('backtestReport.varDisclaimer') }}
        </span>
      </article>

      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.avgWinningTrade') }}</span>
        <strong class="risk-tile__value tone-positive mono">{{ metrics.avgWinningTrade }}</strong>
      </article>

      <article class="risk-tile">
        <span class="risk-tile__label">{{ $t('backtestReport.avgLosingTrade') }}</span>
        <strong class="risk-tile__value tone-negative mono">{{ metrics.avgLosingTrade }}</strong>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { RiskMetrics as RiskMetricsData } from '../../lib/backtestComputed'

defineProps<{
  metrics: RiskMetricsData
}>()

function toneFromValue(value: string): string {
  if (value === '--') return ''
  const n = parseFloat(value)
  if (Number.isNaN(n)) return ''
  if (n > 0) return 'tone-positive'
  if (n < 0) return 'tone-negative'
  return ''
}
</script>

<style scoped>
.risk-panel {
  display: grid;
  gap: 16px;
  padding: 22px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.risk-panel::after {
  content: "";
  position: absolute;
  height: 6px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-danger);
  border-radius: 0 0 14px 14px;
  opacity: 0.9;
}

.risk-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.risk-panel__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.risk-panel__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  position: relative;
  z-index: 1;
}

.risk-tile {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border-light);
}

.risk-tile__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.risk-tile__value {
  font-size: var(--font-size-md);
  font-weight: 800;
  color: var(--color-text-primary);
}

.risk-tile__disclaimer {
  font-size: 11px;
  color: var(--color-warning);
  line-height: 1.4;
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.tone-positive { color: var(--color-positive); }
.tone-negative { color: var(--color-negative); }

@media (max-width: 900px) {
  .risk-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .risk-grid { grid-template-columns: 1fr; }
}
</style>
