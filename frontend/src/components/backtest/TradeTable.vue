<template>
  <details class="trade-table-card">
    <summary class="trade-summary">
      <div class="trade-summary__left">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 3h5v5"/><path d="M21 3l-7 7"/><path d="M8 21H3v-5"/><path d="M3 21l7-7"/></svg>
        {{ $t('tradeTable.title') }}
      </div>
      <span class="trade-count">{{ $t('tradeTable.count', { count: trades.length }) }}</span>
    </summary>
    <div class="trade-content">
      <div v-if="!trades.length" class="trade-empty">
        {{ $t('tradeTable.noTrades') }}
      </div>
      <div v-else class="table-wrapper">
        <table class="trade-list">
          <thead>
            <tr>
              <th>{{ $t('tradeTable.time') }}</th>
              <th>{{ $t('tradeTable.side') }}</th>
              <th>{{ $t('tradeTable.symbol') }}</th>
              <th class="num">{{ $t('tradeTable.price') }}</th>
              <th class="num">{{ $t('tradeTable.quantity') }}</th>
              <th class="num">{{ $t('tradeTable.pnl') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(trade, index) in displayedTrades" :key="trade.id ?? index">
              <td class="mono">{{ formatTimestamp(trade.timestamp) }}</td>
              <td>
                <span :class="['side-badge', trade.side]">
                  {{ trade.side === 'buy' ? $t('tradeTable.buy') : $t('tradeTable.sell') }}
                </span>
              </td>
              <td>{{ trade.symbol }}</td>
              <td class="num mono">{{ formatNumber(trade.price) }}</td>
              <td class="num mono">{{ formatNumber(trade.quantity, 4) }}</td>
              <td :class="['num', 'mono', pnlClass(trade.pnl)]">
                {{ trade.pnl !== undefined ? formatPnl(trade.pnl) : '--' }}
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="trades.length > pageSize" class="pagination">
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

const props = defineProps<{
  trades: Trade[]
}>()

const pageSize = 20
const page = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(props.trades.length / pageSize)))

const displayedTrades = computed(() => {
  const start = (page.value - 1) * pageSize
  return props.trades.slice(start, start + pageSize)
})

function formatTimestamp(ts: number | string): string {
  const ms = typeof ts === 'number'
    ? (ts > 1e12 ? ts : ts * 1000)
    : Date.parse(String(ts))
  if (Number.isNaN(ms)) return String(ts)
  return new Date(ms).toLocaleString(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatNumber(value: number, digits = 2): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  })
}

function formatPnl(value: number): string {
  const prefix = value > 0 ? '+' : ''
  return prefix + formatNumber(value)
}

function pnlClass(pnl?: number): string {
  if (pnl === undefined) return ''
  if (pnl > 0) return 'positive'
  if (pnl < 0) return 'negative'
  return ''
}
</script>

<style scoped>
.trade-table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
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
  border-bottom: 1px solid transparent;
  transition: background 0.15s;
  list-style: none;
  color: var(--color-text-primary);
  font-weight: 700;
  font-size: var(--font-size-sm);
}

.trade-summary::-webkit-details-marker {
  display: none;
}

.trade-table-card[open] .trade-summary {
  border-bottom-color: var(--color-border-light);
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
  color: var(--color-accent);
}

.trade-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  background: var(--color-surface-active);
  padding: 3px 10px;
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

.trade-list {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.trade-list th {
  text-align: left;
  padding: 8px 12px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.trade-list td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border-light);
  color: var(--color-text-primary);
  white-space: nowrap;
}

.trade-list tbody tr:last-child td {
  border-bottom: none;
}

.trade-list tbody tr:hover {
  background: var(--color-surface-hover);
}

.trade-list th.num,
.trade-list td.num {
  text-align: right;
}

.mono {
  font-family: 'Space Mono', monospace;
  font-variant-numeric: tabular-nums;
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
  background: rgba(22, 163, 106, 0.12);
  color: #16a34a;
}

.side-badge.sell {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.positive {
  color: #16a34a;
}

.negative {
  color: #dc2626;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
  margin-top: var(--spacing-sm);
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-primary-border);
  color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .trade-content {
    padding: var(--spacing-sm);
  }

  .trade-list th,
  .trade-list td {
    padding: 6px 8px;
    font-size: var(--font-size-xs);
  }
}
</style>
