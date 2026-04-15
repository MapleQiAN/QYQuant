<template>
  <section class="signal-list-card">
    <div class="signal-list-card__header">
      <div>
        <h3 class="signal-list-card__title">{{ $t('backtestReport.signalListTitle') }}</h3>
        <p class="signal-list-card__subtitle">{{ $t('backtestReport.signalListSubtitle') }}</p>
      </div>
      <span class="signal-list-card__count">{{ $t('backtestReport.signalListCount', { count: signals.length }) }}</span>
    </div>

    <div v-if="!sortedSignals.length" class="signal-list-card__empty">
      {{ $t('backtestReport.signalListEmpty') }}
    </div>

    <div v-else class="signal-list">
      <article v-for="signal in sortedSignals" :key="signal.id" class="signal-item">
        <div class="signal-item__main">
          <span :class="['side-badge', signal.side]">
            {{ signal.side === 'buy' ? $t('tradeTable.buy') : $t('tradeTable.sell') }}
          </span>
          <strong class="signal-item__price mono">{{ formatNumber(signal.price) }}</strong>
          <span class="signal-item__time mono">{{ formatTimestamp(signal.timestamp) }}</span>
        </div>

        <div class="signal-item__meta">
          <span>{{ signal.symbol }}</span>
          <span>{{ $t('backtestReport.tradeQuantityLabel') }} {{ formatNumber(signal.quantity, 4) }}</span>
          <span v-if="signal.pnl !== undefined" :class="pnlClass(signal.pnl)">
            {{ $t('backtestReport.tradePnlLabel') }} {{ formatPnl(signal.pnl) }}
          </span>
          <span
            v-if="durations.has(signalIndexMap.get(signal.id) ?? -1)"
            class="signal-item__duration"
          >
            {{ $t('backtestReport.holdingDays') }} {{ durations.get(signalIndexMap.get(signal.id)!) }}
          </span>
          <span
            v-if="cumReturns[signalIndexMap.get(signal.id) ?? -1] !== undefined"
            :class="['signal-item__cumulative', cumulativeClass(signalIndexMap.get(signal.id)!)]"
          >
            {{ $t('backtestReport.cumulativeReturn') }} {{ formatPnl(cumReturns[signalIndexMap.get(signal.id)!]) }}
          </span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TradeMarker } from '../../lib/chartIndicators'

const props = defineProps<{
  signals: TradeMarker[]
  holdingDurations?: Map<number, number>
  cumulativeReturns?: number[]
}>()

const durations = computed(() => props.holdingDurations ?? new Map<number, number>())
const cumReturns = computed(() => props.cumulativeReturns ?? [])

const sortedSignals = computed(() =>
  [...props.signals].sort((left, right) => right.epochMs - left.epochMs),
)

const signalIndexMap = computed(() => {
  const map = new Map<string, number>()
  props.signals.forEach((s, i) => map.set(s.id, i))
  return map
})

function formatTimestamp(ts: number | string): string {
  const ms = typeof ts === 'number'
    ? (ts > 1e12 ? ts : ts * 1000)
    : Date.parse(String(ts))

  if (Number.isNaN(ms)) {
    return String(ts)
  }

  return new Date(ms).toLocaleString(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatNumber(value: number, digits = 2): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

function formatPnl(value: number): string {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${formatNumber(value)}`
}

function pnlClass(value: number): string {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}

function cumulativeClass(index: number): string {
  const val = cumReturns.value[index]
  if (val === undefined) return ''
  if (val > 0) return 'cumulative-positive'
  if (val < 0) return 'cumulative-negative'
  return ''
}
</script>

<style scoped>
.signal-list-card {
  display: grid;
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background:
    radial-gradient(circle at top right, rgba(54, 214, 182, 0.08), transparent 38%),
    rgba(255, 255, 255, 0.02);
}

.signal-list-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.signal-list-card__title {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.signal-list-card__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.signal-list-card__count {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--color-surface-active);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  white-space: nowrap;
}

.signal-list-card__empty {
  padding: 20px 12px;
  border-radius: 14px;
  text-align: center;
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.02);
}

.signal-list {
  display: grid;
  gap: 10px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.signal-item {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid var(--color-border-light);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
}

.signal-item__main,
.signal-item__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.signal-item__price {
  color: var(--color-text-primary);
  font-size: var(--font-size-md);
}

.signal-item__time,
.signal-item__meta {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.signal-item__duration {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(139, 92, 246, 0.08);
}

.signal-item__cumulative {
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: 6px;
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.cumulative-positive {
  color: var(--color-up);
  background: var(--color-up-bg);
}

.cumulative-negative {
  color: var(--color-down);
  background: var(--color-down-bg);
}

.side-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.side-badge.buy {
  background: var(--color-up-bg);
  color: var(--color-up);
}

.side-badge.sell {
  background: var(--color-down-bg);
  color: var(--color-down);
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.positive {
  color: var(--color-up);
}

.negative {
  color: var(--color-down);
}

@media (max-width: 768px) {
  .signal-list-card__header {
    flex-direction: column;
  }

  .signal-list {
    max-height: none;
  }
}
</style>
