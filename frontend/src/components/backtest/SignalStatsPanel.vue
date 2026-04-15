<template>
  <section class="signal-stats">
    <div class="signal-stats__header">
      <h3 class="signal-stats__title">{{ $t('backtestReport.signalStatsTitle') }}</h3>
      <p class="signal-stats__subtitle">{{ $t('backtestReport.signalStatsSubtitle') }}</p>
    </div>

    <div class="stats-grid">
      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.buyCount') }}</span>
        <strong class="stat-tile__value tone-positive">{{ stats.buyCount }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.sellCount') }}</span>
        <strong class="stat-tile__value tone-negative">{{ stats.sellCount }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.buySellRatio') }}</span>
        <strong class="stat-tile__value mono">{{ stats.buySellRatio }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.buyWinRate') }}</span>
        <strong class="stat-tile__value mono">{{ stats.buyWinRate }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.sellWinRate') }}</span>
        <strong class="stat-tile__value mono">{{ stats.sellWinRate }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.avgBuyPnl') }}</span>
        <strong class="stat-tile__value mono">{{ stats.avgBuyPnl }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.avgSellPnl') }}</span>
        <strong class="stat-tile__value mono">{{ stats.avgSellPnl }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.bestTrade') }}</span>
        <strong class="stat-tile__value tone-positive mono">{{ stats.bestTrade ? `+${stats.bestTrade.pnl.toFixed(2)}` : '--' }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.worstTrade') }}</span>
        <strong class="stat-tile__value tone-negative mono">{{ stats.worstTrade ? stats.worstTrade.pnl.toFixed(2) : '--' }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.signalFrequencyDaily') }}</span>
        <strong class="stat-tile__value mono">{{ stats.signalFrequencyDaily }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.signalFrequencyWeekly') }}</span>
        <strong class="stat-tile__value mono">{{ stats.signalFrequencyWeekly }}</strong>
      </article>

      <article class="stat-tile">
        <span class="stat-tile__label">{{ $t('backtestReport.avgHoldingPeriod') }}</span>
        <strong class="stat-tile__value mono">{{ stats.avgHoldingPeriod }}</strong>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SignalStats } from '../../lib/backtestComputed'

defineProps<{
  stats: SignalStats
}>()
</script>

<style scoped>
.signal-stats {
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

.signal-stats::before {
  content: "";
  position: absolute;
  width: 8px;
  left: 0;
  top: 20px;
  bottom: 20px;
  background: var(--color-accent);
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
  opacity: 0.9;
}

.signal-stats__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.signal-stats__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.signal-stats__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  position: relative;
  z-index: 1;
}

.stat-tile {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border-light);
}

.stat-tile__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.stat-tile__value {
  font-size: var(--font-size-md);
  font-weight: 800;
  color: var(--color-text-primary);
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.tone-positive { color: var(--color-positive); }
.tone-negative { color: var(--color-negative); }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
