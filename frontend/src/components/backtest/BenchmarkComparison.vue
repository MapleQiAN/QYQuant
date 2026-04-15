<template>
  <section class="benchmark-panel">
    <div class="benchmark-panel__header">
      <h3 class="benchmark-panel__title">{{ $t('backtestReport.benchmarkComparisonTitle') }}</h3>
      <p class="benchmark-panel__subtitle">{{ $t('backtestReport.benchmarkComparisonSubtitle') }}</p>
    </div>

    <div class="benchmark-grid">
      <article class="benchmark-tile">
        <span class="benchmark-tile__label">{{ $t('backtestReport.benchmarkTotalReturn') }}</span>
        <strong :class="['benchmark-tile__value', 'mono', toneClass(data.benchmarkTotalReturn)]">
          {{ formatPct(data.benchmarkTotalReturn) }}
        </strong>
      </article>

      <article class="benchmark-tile">
        <span class="benchmark-tile__label">{{ $t('backtestReport.excessReturn') }}</span>
        <strong :class="['benchmark-tile__value', 'mono', toneClass(data.excessReturn)]">
          {{ formatPct(data.excessReturn, true) }}
        </strong>
      </article>

      <article class="benchmark-tile">
        <span class="benchmark-tile__label">{{ $t('backtestReport.trackingError') }}</span>
        <strong class="benchmark-tile__value mono">{{ formatPct(data.trackingError) }}</strong>
      </article>

      <article class="benchmark-tile">
        <span class="benchmark-tile__label">{{ $t('backtestReport.informationRatio') }}</span>
        <strong :class="['benchmark-tile__value', 'mono', toneClass(data.informationRatio)]">
          {{ formatVal(data.informationRatio) }}
        </strong>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { BenchmarkComparison as BenchmarkData } from '../../lib/backtestComputed'

defineProps<{
  data: BenchmarkData
}>()

function formatPct(value: number | null, showSign = false): string {
  if (value === null) return '--'
  const sign = showSign && value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function formatVal(value: number | null): string {
  if (value === null) return '--'
  return value.toFixed(3)
}

function toneClass(value: number | null): string {
  if (value === null) return ''
  if (value > 0) return 'tone-positive'
  if (value < 0) return 'tone-negative'
  return ''
}
</script>

<style scoped>
.benchmark-panel {
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

.benchmark-panel::before {
  content: "";
  position: absolute;
  width: 44px;
  height: 44px;
  background: var(--color-primary);
  bottom: -14px;
  left: -14px;
  transform: rotate(25deg);
  border-radius: 10px;
  opacity: 0.85;
}

.benchmark-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.benchmark-panel__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.benchmark-panel__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.benchmark-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  position: relative;
  z-index: 1;
}

.benchmark-tile {
  display: grid;
  gap: 4px;
  padding: 14px;
  border-radius: var(--radius-sm);
  background: #fafafa;
  border: 2px solid var(--color-border-light);
}

.benchmark-tile__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.benchmark-tile__value {
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.tone-positive { color: var(--color-positive); }
.tone-negative { color: var(--color-negative); }

@media (max-width: 640px) {
  .benchmark-grid { grid-template-columns: 1fr; }
}
</style>
