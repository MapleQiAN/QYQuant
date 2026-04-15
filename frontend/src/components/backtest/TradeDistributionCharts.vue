<template>
  <section class="distribution-panel">
    <div class="distribution-panel__header">
      <h3 class="distribution-panel__title">{{ $t('backtestReport.tradeDistributionTitle') }}</h3>
      <p class="distribution-panel__subtitle">{{ $t('backtestReport.tradeDistributionSubtitle') }}</p>
    </div>

    <div class="distribution-charts">
      <div class="chart-card">
        <h4 class="chart-card__title">{{ $t('backtestReport.pnlDistribution') }}</h4>
        <div ref="pnlChartRef" class="chart-canvas"></div>
        <div v-if="!distribution.pnlHistogramBuckets.length" class="chart-empty">
          --
        </div>
      </div>

      <div class="chart-card">
        <h4 class="chart-card__title">{{ $t('backtestReport.holdingDuration') }}</h4>
        <div ref="durationChartRef" class="chart-canvas"></div>
        <div v-if="!distribution.holdingDurationBuckets.length" class="chart-empty">
          --
        </div>
      </div>

      <div class="chart-card">
        <h4 class="chart-card__title">{{ $t('backtestReport.monthlyReturns') }}</h4>
        <div ref="monthlyChartRef" class="chart-canvas"></div>
        <div v-if="!distribution.monthlyReturns.length" class="chart-empty">
          --
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '../../stores/user'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import type { TradeDistribution } from '../../lib/backtestComputed'

const props = defineProps<{
  distribution: TradeDistribution
}>()

const { locale } = useI18n()
const userStore = useUserStore()

const pnlChartRef = ref<HTMLDivElement | null>(null)
const durationChartRef = ref<HTMLDivElement | null>(null)
const monthlyChartRef = ref<HTMLDivElement | null>(null)

const pnlChart = ref<ECharts | null>(null)
const durationChart = ref<ECharts | null>(null)
const monthlyChart = ref<ECharts | null>(null)

let resizeObserver: ResizeObserver | null = null

function buildPnlOption(): EChartsOption {
  const buckets = props.distribution.pnlHistogramBuckets
  if (!buckets.length) {
    return { title: { text: '--', left: 'center', top: 'middle', textStyle: { color: '#64748b', fontSize: 14 } } }
  }

  return {
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '5%', top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: buckets.map((b) => b.range),
      axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    series: [{
      type: 'bar',
      data: buckets.map((b) => ({
        value: b.count,
        itemStyle: { color: '#1976d2', borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 32
    }]
  }
}

function buildDurationOption(): EChartsOption {
  const buckets = props.distribution.holdingDurationBuckets
  if (!buckets.length) {
    return { title: { text: '--', left: 'center', top: 'middle', textStyle: { color: '#64748b', fontSize: 14 } } }
  }

  return {
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '5%', top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: buckets.map((b) => b.range),
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    series: [{
      type: 'bar',
      data: buckets.map((b) => ({
        value: b.count,
        itemStyle: { color: '#f9a825', borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 32
    }]
  }
}

function buildMonthlyOption(): EChartsOption {
  const months = props.distribution.monthlyReturns
  if (!months.length) {
    return { title: { text: '--', left: 'center', top: 'middle', textStyle: { color: '#64748b', fontSize: 14 } } }
  }

  const upCol = typeof window !== 'undefined'
    ? getComputedStyle(document.documentElement).getPropertyValue('--color-up').trim() || '#d4393b'
    : '#d4393b'
  const downCol = typeof window !== 'undefined'
    ? getComputedStyle(document.documentElement).getPropertyValue('--color-down').trim() || '#2e7d32'
    : '#2e7d32'

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => Number(value).toFixed(2) + '%'
    },
    grid: { left: '10%', right: '5%', top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: months.map((m) => m.month),
      axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#64748b',
        formatter: (value: number) => value.toFixed(1) + '%'
      },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 }
    ],
    series: [{
      type: 'bar',
      data: months.map((m) => ({
        value: m.returnPct ?? 0,
        itemStyle: {
          color: (m.returnPct ?? 0) >= 0 ? upCol : downCol,
          borderRadius: [4, 4, 0, 0]
        }
      })),
      barMaxWidth: 28
    }]
  }
}

function renderCharts() {
  pnlChart.value?.setOption(buildPnlOption(), true)
  durationChart.value?.setOption(buildDurationOption(), true)
  monthlyChart.value?.setOption(buildMonthlyOption(), true)
}

function initChart(el: HTMLDivElement | null): ECharts | null {
  if (!el) return null
  const instance = echarts.init(el)
  return instance
}

onMounted(() => {
  pnlChart.value = initChart(pnlChartRef.value)
  durationChart.value = initChart(durationChartRef.value)
  monthlyChart.value = initChart(monthlyChartRef.value)
  renderCharts()

  const observeTarget = pnlChartRef.value?.parentElement
  if (typeof ResizeObserver !== 'undefined' && observeTarget) {
    resizeObserver = new ResizeObserver(() => {
      pnlChart.value?.resize()
      durationChart.value?.resize()
      monthlyChart.value?.resize()
    })
    resizeObserver.observe(observeTarget)
  }
})

watch(() => [props.distribution, locale.value, userStore.marketStyle], () => {
  renderCharts()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  pnlChart.value?.dispose()
  durationChart.value?.dispose()
  monthlyChart.value?.dispose()
  pnlChart.value = null
  durationChart.value = null
  monthlyChart.value = null
})
</script>

<style scoped>
.distribution-panel {
  display: grid;
  gap: 16px;
  padding: 22px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.distribution-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.distribution-panel__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.distribution-panel__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.distribution-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.chart-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border-light);
  background: #fafafa;
}

.chart-card__title {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 700;
}

.chart-canvas {
  width: 100%;
  height: 200px;
}

.chart-empty {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

@media (max-width: 768px) {
  .chart-canvas { height: 160px; }
  .chart-empty { height: 160px; }
}
</style>
