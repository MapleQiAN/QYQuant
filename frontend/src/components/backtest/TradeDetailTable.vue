<template>
  <details class="trade-table-card" open>
    <summary class="trade-summary">
      <div class="trade-summary__left">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        {{ $t('tradeDetail.title') }}
      </div>
      <span class="trade-count">{{ $t('tradeDetail.count', { count: pairedTrades.length }) }}</span>
    </summary>
    <div class="trade-content">
      <div v-if="!pairedTrades.length" class="trade-empty">
        {{ $t('tradeDetail.noTrades') }}
      </div>
      <div v-else class="table-wrapper">
        <table class="trade-detail-list">
          <thead>
            <tr>
              <th class="num">#</th>
              <th>{{ $t('tradeDetail.direction') }}</th>
              <th>{{ $t('tradeDetail.openTime') }}</th>
              <th>{{ $t('tradeDetail.closeTime') }}</th>
              <th class="num">{{ $t('tradeDetail.openPrice') }}</th>
              <th class="num">{{ $t('tradeDetail.closePrice') }}</th>
              <th class="num">{{ $t('tradeDetail.return') }}</th>
              <th class="num">{{ $t('tradeDetail.holdingDays') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(trade, index) in displayedTrades" :key="index">
              <td class="num mono">{{ offset + index + 1 }}</td>
              <td>
                <span :class="['direction-badge', trade.direction]">
                  <span class="direction-dot"></span>
                  {{ trade.direction === 'long' ? $t('tradeDetail.long') : $t('tradeDetail.short') }}
                </span>
              </td>
              <td class="mono">{{ formatDate(trade.openTime) }}</td>
              <td class="mono">{{ formatDate(trade.closeTime) }}</td>
              <td class="num mono">{{ formatPrice(trade.openPrice) }}</td>
              <td class="num mono">{{ formatPrice(trade.closePrice) }}</td>
              <td :class="['num', 'mono', pnlClass(trade.returnPct)]">
                {{ formatReturn(trade.returnPct) }}
              </td>
              <td class="num mono">{{ trade.holdingDays }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="pairedTrades.length > pageSize" class="pagination">
          <button class="page-btn" :disabled="page <= 1" @click="page--">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="page++">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
      </div>
    </div>
  </details>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Trade } from '../../types/Trade'

interface PairedTrade {
  direction: 'long' | 'short'
  openTime: number
  closeTime: number
  openPrice: number
  closePrice: number
  returnPct: number
  holdingDays: number
}

const props = defineProps<{
  trades: Trade[]
}>()

const pageSize = 20
const page = ref(1)

const pairedTrades = computed<PairedTrade[]>(() => {
  const result: PairedTrade[] = []
  const list = props.trades
  if (!list.length) return result

  let i = 0
  while (i < list.length - 1) {
    const open = list[i]
    const close = list[i + 1]

    const openTs = toMs(open.timestamp)
    const closeTs = toMs(close.timestamp)
    const holdingDays = Math.max(1, Math.round((closeTs - openTs) / (1000 * 60 * 60 * 24)))

    if (open.side === 'buy' && close.side === 'sell') {
      const returnPct = open.price !== 0
        ? ((close.price - open.price) / open.price) * 100
        : 0
      result.push({
        direction: 'long',
        openTime: openTs,
        closeTime: closeTs,
        openPrice: open.price,
        closePrice: close.price,
        returnPct,
        holdingDays,
      })
      i += 2
    } else if (open.side === 'sell' && close.side === 'buy') {
      const returnPct = open.price !== 0
        ? ((open.price - close.price) / open.price) * 100
        : 0
      result.push({
        direction: 'short',
        openTime: openTs,
        closeTime: closeTs,
        openPrice: open.price,
        closePrice: close.price,
        returnPct,
        holdingDays,
      })
      i += 2
    } else {
      i++
    }
  }

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(pairedTrades.value.length / pageSize)))

const offset = computed(() => (page.value - 1) * pageSize)

const displayedTrades = computed(() => {
  return pairedTrades.value.slice(offset.value, offset.value + pageSize)
})

function toMs(ts: number | string): number {
  if (typeof ts === 'number') return ts > 1e12 ? ts : ts * 1000
  const ms = Date.parse(String(ts))
  return Number.isNaN(ms) ? 0 : ms
}

function formatDate(ts: number): string {
  if (!ts) return '--'
  const d = new Date(ts)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatPrice(value: number): string {
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function formatReturn(value: number): string {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)}%`
}

function pnlClass(value: number): string {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}
</script>

<style scoped>
.trade-table-card {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  margin-bottom: var(--spacing-lg);
}

.trade-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  user-select: none;
  background: var(--color-surface-elevated);
  border-bottom: 2px solid transparent;
  transition: background 0.15s;
  list-style: none;
  color: var(--color-text-primary);
  font-weight: 800;
  font-size: var(--font-size-sm);
}

.trade-summary::-webkit-details-marker {
  display: none;
}

.trade-table-card[open] .trade-summary {
  border-bottom-color: var(--color-border);
}

.trade-summary:hover {
  background: var(--color-surface-hover);
}

.trade-summary__left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary);
}

.trade-summary__left svg {
  color: var(--color-primary);
}

.trade-count {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  background: var(--color-surface-active);
  padding: 3px 10px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
}

.trade-content {
  padding: var(--spacing-md) var(--spacing-lg);
}

.trade-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  padding: var(--spacing-xl) 0;
}

.table-wrapper {
  overflow-x: auto;
}

.trade-detail-list {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.trade-detail-list th {
  text-align: left;
  padding: 10px 12px;
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  white-space: nowrap;
}

.trade-detail-list td {
  padding: 10px 12px;
  border-bottom: 2px dashed var(--color-border-light);
  color: var(--color-text-primary);
  white-space: nowrap;
}

.trade-detail-list tbody tr:last-child td {
  border-bottom: none;
}

.trade-detail-list tbody tr:hover {
  background: var(--color-surface-hover);
}

.trade-detail-list th.num,
.trade-detail-list td.num {
  text-align: right;
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.direction-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.direction-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.direction-badge.long .direction-dot {
  background: var(--color-positive);
}

.direction-badge.short .direction-dot {
  background: var(--color-negative);
}

.positive {
  color: var(--color-positive);
}

.negative {
  color: var(--color-negative);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 2px dashed var(--color-border-light);
  margin-top: var(--spacing-sm);
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

@media (max-width: 640px) {
  .trade-content {
    padding: var(--spacing-sm);
  }

  .trade-detail-list th,
  .trade-detail-list td {
    padding: 6px 8px;
    font-size: var(--font-size-xs);
  }
}
</style>
