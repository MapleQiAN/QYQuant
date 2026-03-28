<template>
  <div class="backtest-card card">
    <SkeletonState v-if="loading" :lines="8" />
    <ErrorState
      v-else-if="error"
      :message="error"
      :action-label="$t('common.retry')"
      @retry="$emit('retry')"
    />
    <EmptyState v-else-if="!data" />
    <template v-else>
      <div class="card-header">
        <div class="header-left">
          <h3 class="card-title">{{ $t('backtest.title') }}</h3>
          <span class="badge badge-success">{{ $t('backtest.statusCompleted') }}</span>
          <span class="badge badge-info">{{ dataSourceBadge }}</span>
        </div>
        <div class="header-actions">
          <div class="data-source-control">
            <span class="data-source-label">{{ $t('backtest.dataSource') }}</span>
            <select
              class="data-source-select"
              :value="selectedDataSource"
              @change="handleDataSourceChange"
            >
              <option v-for="option in dataSourceOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <button class="btn btn-secondary" @click="emit('refresh')">
            <RefreshIcon />
            {{ $t('backtest.refresh') }}
          </button>
          <button class="btn btn-primary" type="button" data-test="backtest-export" @click="handleExport">
            <ExportIcon />
            {{ $t('backtest.export') }}
          </button>
        </div>
      </div>

      <div class="kpi-grid">
        <StatCard
          :label="$t('backtest.kpiTotalReturn')"
          :value="kpis.totalReturn"
          suffix="%"
          :change="kpis.totalReturn"
          :showSign="true"
          variant="up"
        >
          <template #icon>
            <TrendUpIcon />
          </template>
        </StatCard>

        <StatCard
          :label="$t('backtest.kpiAnnualizedReturn')"
          :value="kpis.annualizedReturn"
          suffix="%"
          variant="info"
        >
          <template #icon>
            <CalendarIcon />
          </template>
        </StatCard>

        <StatCard
          :label="$t('backtest.kpiSharpe')"
          :value="kpis.sharpeRatio"
          variant="default"
        >
          <template #icon>
            <TargetIcon />
          </template>
        </StatCard>

        <StatCard
          :label="$t('backtest.kpiMaxDrawdown')"
          :value="kpis.maxDrawdown"
          suffix="%"
          :showSign="true"
          variant="down"
        >
          <template #icon>
            <TrendDownIcon />
          </template>
        </StatCard>
      </div>

      <div class="chart-section">
        <KlinePlaceholder
          :data="klineData"
          :trades="tradeData"
          :symbol="symbol"
          :timeframe="timeframe"
          @timeframe-change="handleTimeframeChange"
        />
      </div>

      <div class="secondary-stats">
        <div class="stat-item">
          <span class="stat-label">{{ $t('backtest.statWinRate') }}</span>
          <span class="stat-value">{{ kpis.winRate }}%</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ $t('backtest.statProfitFactor') }}</span>
          <span class="stat-value">{{ kpis.profitFactor }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ $t('backtest.statTotalTrades') }}</span>
          <span class="stat-value">{{ kpis.totalTrades }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ $t('backtest.statAvgHolding') }}</span>
          <span class="stat-value">{{ kpis.avgHoldingDays }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { downloadJson } from '../lib/download'
import type { BacktestLatestResponse } from '../types/Backtest'
import type { KlineBar } from '../types/KlineBar'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'
import KlinePlaceholder from './KlinePlaceholder.vue'
import SkeletonState from './SkeletonState.vue'
import StatCard from './StatCard.vue'

const emit = defineEmits<{
  (event: 'retry'): void
  (event: 'refresh'): void
  (event: 'data-source-change', value: string): void
  (event: 'timeframe-change', value: string): void
}>()

const props = withDefaults(defineProps<{
  data: BacktestLatestResponse | null
  loading?: boolean
  error?: string | null
  symbol?: string
  timeframe?: string
  dataSource?: string
}>(), {
  loading: false,
  error: null,
  symbol: 'XAUUSD',
  timeframe: '15m',
  dataSource: 'auto'
})

const { t } = useI18n()

const kpis = computed(() => ({
  totalReturn: props.data?.summary.totalReturn ?? 0,
  annualizedReturn: props.data?.summary.annualizedReturn ?? 0,
  sharpeRatio: props.data?.summary.sharpeRatio ?? 0,
  maxDrawdown: props.data?.summary.maxDrawdown ?? 0,
  winRate: props.data?.summary.winRate ?? 0,
  profitFactor: props.data?.summary.profitFactor ?? 0,
  totalTrades: props.data?.summary.totalTrades ?? 0,
  avgHoldingDays: props.data?.summary.avgHoldingDays ?? 0
}))

const klineData = computed<KlineBar[]>(() => props.data?.kline ?? [])
const tradeData = computed(() => props.data?.trades ?? [])
const selectedDataSource = computed(() => normalizeDataSource(props.dataSource) ?? 'auto')
const resolvedDataSource = computed(() => normalizeDataSource(props.data?.dataSource) ?? selectedDataSource.value)

const dataSourceOptions = computed(() => ([
  { value: 'auto', label: t('backtest.dataSourceAuto') },
  { value: 'binance', label: t('backtest.dataSourceBinance') },
  { value: 'freegold', label: t('backtest.dataSourceFreegold') },
  { value: 'mock', label: t('backtest.dataSourceMock') }
]))

const dataSourceBadge = computed(() => {
  const resolved = resolvedDataSource.value
  const resolvedLabel = dataSourceOptions.value.find((option) => option.value === resolved)?.label ?? resolved
  if (selectedDataSource.value === 'auto' && resolved !== 'auto') {
    return t('backtest.dataSourceAutoWith', { source: resolvedLabel })
  }
  return resolvedLabel
})

const handleDataSourceChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('data-source-change', target.value)
}

const handleTimeframeChange = (value: string) => {
  emit('timeframe-change', value)
}

const handleExport = () => {
  if (!props.data) {
    return
  }

  downloadJson(`backtest-${props.symbol}-${props.timeframe}-${Date.now()}.json`, {
    symbol: props.symbol,
    timeframe: props.timeframe,
    requestedDataSource: selectedDataSource.value,
    exportedAt: new Date().toISOString(),
    ...props.data
  })
}

function normalizeDataSource(value?: string | null) {
  if (!value) return null
  const normalized = String(value).trim().toLowerCase()
  return normalized || null
}

const RefreshIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8' }),
  h('path', { d: 'M21 3v5h-5' }),
  h('path', { d: 'M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16' }),
  h('path', { d: 'M8 16H3v5' })
])

const ExportIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' }),
  h('polyline', { points: '17 8 12 3 7 8' }),
  h('line', { x1: 12, y1: 3, x2: 12, y2: 15 })
])

const TrendUpIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('polyline', { points: '23 6 13.5 15.5 8.5 10.5 1 18' }),
  h('polyline', { points: '17 6 23 6 23 12' })
])

const TrendDownIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('polyline', { points: '23 18 13.5 8.5 8.5 13.5 1 6' }),
  h('polyline', { points: '17 18 23 18 23 12' })
])

const CalendarIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('rect', { x: 3, y: 4, width: 18, height: 18, rx: 2, ry: 2 }),
  h('line', { x1: 16, y1: 2, x2: 16, y2: 6 }),
  h('line', { x1: 8, y1: 2, x2: 8, y2: 6 }),
  h('line', { x1: 3, y1: 10, x2: 21, y2: 10 })
])

const TargetIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('circle', { cx: 12, cy: 12, r: 6 }),
  h('circle', { cx: 12, cy: 12, r: 2 })
])
</script>

<style scoped>
.backtest-card {
  padding: var(--spacing-lg);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.data-source-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.data-source-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.data-source-select {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  outline: none;
  cursor: pointer;
}

.data-source-select:focus {
  border-color: var(--color-primary);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.chart-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.secondary-stats {
  display: flex;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-item .stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.stat-item .stat-value {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-feature-settings: "tnum" 1;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1024px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .secondary-stats {
    flex-wrap: wrap;
  }
}
</style>
