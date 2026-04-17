<template>
  <div class="progress-card card">
    <div class="card-header">
      <h3 class="card-title">
        <ChartIcon class="title-icon" />
        {{ $t('progress.title') }}
      </h3>
      <QSelect
        v-model="selectedPeriod"
        :options="periodOptions"
        size="sm"
      />
    </div>

    <div class="stats-grid">
      <div class="stat-block">
        <div class="stat-header">
          <span class="stat-label">{{ $t('progress.backtestCount') }}</span>
          <span class="stat-value">
            <template v-if="isUnlimited">{{ backtestCount }}/∞</template>
            <template v-else>{{ backtestCount }}/{{ backtestTarget }}</template>
          </span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (isUnlimited ? Math.min(backtestCount / 10 * 100, 100) : backtestProgress) + '%' }"
          ></div>
        </div>
        <div class="stat-footer">
          <span>{{ $t('progress.monthlyQuota') }}</span>
          <span class="highlight">
            <template v-if="isUnlimited">∞</template>
            <template v-else>{{ backtestProgress.toFixed(0) }}%</template>
          </span>
        </div>
      </div>

      <div class="stat-block">
        <div class="stat-header">
          <span class="stat-label">{{ $t('progress.robotRuntime') }}</span>
          <span class="stat-value">{{ totalBots }} {{ $t('progress.runtimeUnit') }}</span>
        </div>
        <div class="runtime-visual">
          <div class="runtime-bar">
            <div
              v-for="i in 7"
              :key="i"
              :class="['bar-segment', { active: i <= activeSegments }]"
            ></div>
          </div>
        </div>
        <div class="stat-footer">
          <span>{{ $t('progress.activeBots') }}</span>
          <span class="highlight">{{ activeBots }}</span>
        </div>
      </div>

      <div class="stat-block profit-block">
        <div class="stat-header">
          <span class="stat-label">{{ $t('progress.totalProfit') }}</span>
          <span :class="['profit-change', { positive: profitChange >= 0 }]">
            {{ profitChange >= 0 ? '+' : '' }}{{ profitChange }}%
          </span>
        </div>
        <div class="profit-value">
          {{ formatCurrency(totalProfit, true) }}
        </div>
        <div class="profit-chart">
          <svg class="mini-chart" viewBox="0 0 120 40" preserveAspectRatio="none">
            <defs>
              <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--color-up)" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="var(--color-up)" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path :d="areaPath" fill="url(#profitGradient)" />
            <path
              :d="linePath"
              fill="none"
              stroke="var(--color-up)"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>
    </div>

    <div class="quick-stats">
      <div class="quick-stat-item">
        <div class="quick-stat-icon success">
          <TrendUpIcon />
        </div>
        <div class="quick-stat-content">
          <span class="quick-stat-value">{{ winRate ? (winRate * 100).toFixed(0) + '%' : '--' }}</span>
          <span class="quick-stat-label">{{ $t('progress.avgWinRate') }}</span>
        </div>
      </div>
      <div class="quick-stat-item">
        <div class="quick-stat-icon info">
          <ClockIcon />
        </div>
        <div class="quick-stat-content">
          <span class="quick-stat-value">{{ avgHolding ? avgHolding.toFixed(1) : '--' }}</span>
          <span class="quick-stat-label">{{ $t('progress.avgHolding') }}</span>
        </div>
      </div>
      <div class="quick-stat-item">
        <div class="quick-stat-icon warning">
          <TargetIcon />
        </div>
        <div class="quick-stat-content">
          <span class="quick-stat-value">{{ sharpeRatio ? sharpeRatio.toFixed(2) : '--' }}</span>
          <span class="quick-stat-label">{{ $t('progress.sharpeRatio') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { QSelect } from './ui'
import type { DashboardStats } from '../api/dashboard'

const props = defineProps<{
  stats?: DashboardStats | null
  loading?: boolean
}>()

const { locale, t } = useI18n()

const selectedPeriod = ref('30d')
const periodOptions = computed(() => [
  { label: t('progress.period7'), value: '7d' },
  { label: t('progress.period30'), value: '30d' },
  { label: t('progress.period90'), value: '90d' },
])

const quota = computed(() => props.stats?.backtest_quota)
const summary = computed(() => props.stats?.latest_summary)

const isUnlimited = computed(() => quota.value?.limit === 'unlimited')
const backtestCount = computed(() => quota.value?.used ?? 0)
const backtestTarget = computed(() => {
  const limit = quota.value?.limit
  return typeof limit === 'number' ? limit : 0
})
const activeBots = computed(() => props.stats?.active_bots ?? 0)
const totalBots = computed(() => props.stats?.total_bots ?? 0)
const totalProfit = computed(() => summary.value?.total_return ?? 0)
const profitChange = computed(() => props.stats?.profit_change ?? 0)
const winRate = computed(() => summary.value?.win_rate ?? 0)
const avgHolding = computed(() => summary.value?.avg_holding_days ?? 0)
const sharpeRatio = computed(() => summary.value?.sharpe_ratio ?? 0)

const backtestProgress = computed(() => {
  if (isUnlimited.value || backtestTarget.value <= 0) return 0
  return Math.min((backtestCount.value / backtestTarget.value) * 100, 100)
})
const activeSegments = computed(() => Math.min(7, Math.ceil((totalBots.value / 7) * 7)))

const chartData = computed(() => props.stats?.profit_history ?? [])

const linePath = computed(() => {
  const data = chartData.value
  if (data.length < 2) return ''
  const width = 120
  const height = 40
  const maxVal = Math.max(...data.map(Math.abs), 1)
  const step = width / (data.length - 1)

  return data.map((value, index) => {
    const x = index * step
    const y = height / 2 - (value / maxVal) * (height / 2)
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
  }).join(' ')
})

const areaPath = computed(() => {
  const data = chartData.value
  if (data.length < 2) return ''
  const width = 120
  const height = 40
  const maxVal = Math.max(...data.map(Math.abs), 1)
  const step = width / (data.length - 1)

  const points = data.map((value, index) => {
    const x = index * step
    const y = height / 2 - (value / maxVal) * (height / 2)
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
  }).join(' ')

  return `${points} L ${width} ${height} L 0 ${height} Z`
})

function formatCurrency(value: number, withDecimals = false) {
  const localeValue = locale.value === 'zh' ? 'zh-CN' : 'en-US'
  const options = withDecimals ? { minimumFractionDigits: 2 } : {}
  return value.toLocaleString(localeValue, options)
}

const ChartIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 3v18h18' }),
  h('path', { d: 'm19 9-5 5-4-4-3 3' })
])

const TrendUpIcon = () => h('svg', {
  width: 16,
  height: 16,
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

const ClockIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('polyline', { points: '12 6 12 12 16 14' })
])

const TargetIcon = () => h('svg', {
  width: 16,
  height: 16,
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
.progress-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.title-icon {
  color: var(--color-primary);
}

.period-select {
  padding: 8px 12px;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.period-select:hover {
  border-color: var(--color-primary-border);
}

.period-select:focus {
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.stats-grid {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.stat-block {
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.stat-block::after {
  content: "";
  position: absolute;
  height: 4px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
  border-radius: 0 0 8px 8px;
}

.stat-block:nth-child(1)::after { background: var(--color-primary); }
.stat-block:nth-child(2)::after { background: var(--color-accent); }
.stat-block:nth-child(3)::after { background: var(--color-up); }

.stat-block:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-sm);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.stat-value {
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.progress-bar {
  height: 8px;
  background: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-md);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
  box-shadow: 0 0 12px rgba(30, 90, 168, 0.3);
}

.stat-footer {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
}

.highlight {
  color: var(--color-accent);
  font-weight: 700;
}

.runtime-visual {
  margin-bottom: var(--spacing-md);
}

.runtime-bar {
  display: flex;
  gap: var(--spacing-sm);
}

.bar-segment {
  flex: 1;
  height: 28px;
  background: var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.bar-segment:hover {
  background: var(--color-border-hover);
}

.bar-segment.active {
  background: linear-gradient(180deg, var(--color-info) 0%, var(--color-info-bg) 100%);
  box-shadow: 0 0 12px rgba(30, 90, 168, 0.2);
}

.profit-block {
  background: var(--color-up-bg);
}

.profit-block:hover {
  background: var(--color-up-bg);
  box-shadow: var(--shadow-sm);
}

.profit-change {
  font-size: var(--font-size-xs);
  font-weight: 800;
  padding: 4px 10px;
  background: var(--color-up-bg);
  color: var(--color-up);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
}

.profit-value {
  font-size: var(--font-size-xxxl);
  font-weight: 800;
  color: var(--color-up);
  margin-bottom: var(--spacing-md);
  letter-spacing: -0.01em;
}

.profit-chart {
  height: 48px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

.quick-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 2px solid var(--color-border);
  margin-top: auto;
  background: var(--color-surface-elevated);
  overflow: hidden;
}

.quick-stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all var(--transition-fast);
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
}

.quick-stat-item:hover {
  background: var(--color-surface-hover);
}

.quick-stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.quick-stat-icon.success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.quick-stat-icon.info {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.quick-stat-icon.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.quick-stat-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.quick-stat-value {
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.quick-stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
</style>
