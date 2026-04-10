<template>
  <div class="equity-chart">
    <div class="chart-meta">
      <div>
        <h3 class="chart-title">{{ $t('equityChart.title') }}</h3>
        <p class="chart-caption">{{ $t('equityChart.caption') }}</p>
      </div>
    </div>
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import type { BacktestReportPoint } from '../../types/Backtest'
import type { Trade } from '../../types/Trade'

const props = withDefaults(defineProps<{
  points: BacktestReportPoint[]
  trades?: Trade[]
}>(), {
  trades: () => []
})

const { t, locale } = useI18n()
const chartRef = ref<HTMLDivElement | null>(null)
const chart = ref<ECharts | null>(null)
let resizeObserver: ResizeObserver | null = null

const tradeMarkers = computed(() => {
  if (!props.points.length) return []

  const sortedPoints = [...props.points].sort((a, b) => a.timestamp - b.timestamp)
  const timestamps = sortedPoints.map((p) => p.timestamp)

  function findNearestEquity(ts: number): number {
    let lo = 0
    let hi = timestamps.length - 1
    while (lo < hi) {
      const mid = (lo + hi) >> 1
      if (timestamps[mid] < ts) lo = mid + 1
      else hi = mid
    }
    if (lo === 0) return sortedPoints[0].equity
    const prev = timestamps[lo - 1]
    const curr = timestamps[lo]
    return (ts - prev <= curr - ts)
      ? sortedPoints[lo - 1].equity
      : sortedPoints[lo].equity
  }

  return (props.trades || []).map((trade) => {
    const timestamp = Number(trade.timestamp)
    const isBuy = trade.side === 'buy'
    const equity = findNearestEquity(timestamp)
    return {
      name: isBuy ? 'Buy' : 'Sell',
      coord: [timestamp, equity],
      value: isBuy ? 'B' : 'S',
      symbol: 'pin',
      symbolSize: 28,
      symbolRotate: isBuy ? 180 : 0,
      symbolOffset: [0, isBuy ? -16 : 16],
      itemStyle: {
        color: isBuy ? '#16a34a' : '#dc2626'
      },
      label: {
        show: true,
        color: '#ffffff',
        formatter: isBuy ? 'B' : 'S',
        fontWeight: 700,
        fontSize: 10,
        offset: isBuy ? [0, 4] : [0, -2]
      }
    }
  })
})

function buildOption(): EChartsOption {
  if (!props.points.length) {
    return {
      title: {
        text: t('equityChart.noData'),
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#64748b',
          fontSize: 14,
          fontWeight: 500
        }
      }
    }
  }

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
    },
    legend: {
      top: 8,
      data: [t('equityChart.strategyEquity'), t('equityChart.benchmark')]
    },
    grid: {
      left: '5%',
      right: '3%',
      top: 48,
      bottom: 52
    },
    xAxis: {
      type: 'time'
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        bottom: 10,
        height: 18
      }
    ],
    series: [
      {
        name: t('equityChart.strategyEquity'),
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#0f766e'
        },
        areaStyle: {
          color: 'rgba(15, 118, 110, 0.10)'
        },
        data: props.points.map((point) => [point.timestamp, point.equity]),
        markPoint: {
          data: tradeMarkers.value
        }
      },
      {
        name: t('equityChart.benchmark'),
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 1.5,
          type: 'dashed',
          color: '#94a3b8'
        },
        data: props.points.map((point) => [point.timestamp, point.benchmark_equity])
      }
    ]
  }
}

function renderChart() {
  if (!chart.value) return
  chart.value.setOption(buildOption(), true)
}

onMounted(() => {
  if (!chartRef.value) return
  chart.value = echarts.init(chartRef.value)
  renderChart()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart.value?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => [props.points, props.trades, locale.value], () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart.value?.dispose()
  chart.value = null
})
</script>

<style scoped>
.equity-chart {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, rgba(15, 118, 110, 0.05), var(--color-surface));
  padding: var(--spacing-md);
}

.chart-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.chart-title {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.chart-caption {
  margin: 4px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.chart-canvas {
  width: 100%;
  height: 420px;
}

@media (max-width: 768px) {
  .chart-canvas {
    height: 340px;
  }
}
</style>
