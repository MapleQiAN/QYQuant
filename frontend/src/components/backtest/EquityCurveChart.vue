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

function findNearestPoint(timestamp: number) {
  if (!props.points.length) {
    return null
  }

  let nearest = props.points[0]
  let smallestGap = Math.abs(props.points[0].timestamp - timestamp)

  for (const point of props.points) {
    const gap = Math.abs(point.timestamp - timestamp)
    if (gap < smallestGap) {
      nearest = point
      smallestGap = gap
    }
  }

  return nearest
}

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

  const upCol = getComputedStyle(document.documentElement).getPropertyValue('--color-up').trim() || '#d4393b'
  const downCol = getComputedStyle(document.documentElement).getPropertyValue('--color-down').trim() || '#2e7d32'

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
        color: isBuy ? upCol : downCol
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

const hasDrawdown = computed(() =>
  props.points.some((point) => point.drawdown !== undefined && point.drawdown !== null)
)

function formatAxisTime(value: string | number) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatTooltipValue(value: unknown) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return '--'
  }
  return numeric.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function buildTooltip(params: any[]) {
  if (!Array.isArray(params) || params.length === 0) {
    return ''
  }

  const axisValue = params[0]?.axisValue
  const currentPoint = findNearestPoint(Number(axisValue))
  const first = props.points[0]
  const strategyReturn =
    first && currentPoint && first.equity
      ? ((currentPoint.equity - first.equity) / first.equity) * 100
      : null
  const benchmarkReturn =
    first && currentPoint && first.benchmark_equity
      ? ((currentPoint.benchmark_equity - first.benchmark_equity) / first.benchmark_equity) * 100
      : null
  const items = params
    .filter((item) => Array.isArray(item.data))
    .map((item) => {
      const rawValue = Array.isArray(item.data) ? item.data[item.data.length - 1] : item.data
      return `<div style="display:flex;justify-content:space-between;gap:12px;">
        <span style="color:${item.color};">${item.seriesName}</span>
        <strong style="color:#111111;">${formatTooltipValue(rawValue)}</strong>
      </div>`
    })
    .join('')

  const contextRows = [
    strategyReturn === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#6b6b6b;">Strategy Return</span>
          <strong style="color:#111111;">${strategyReturn.toFixed(2)}%</strong>
        </div>`,
    benchmarkReturn === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#6b6b6b;">Benchmark Return</span>
          <strong style="color:#111111;">${benchmarkReturn.toFixed(2)}%</strong>
        </div>`,
    currentPoint?.drawdown === undefined || currentPoint?.drawdown === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#6b6b6b;">Drawdown</span>
          <strong style="color:#111111;">${Number(currentPoint.drawdown).toFixed(2)}%</strong>
        </div>`
  ].filter(Boolean).join('')

  return `<div style="min-width:190px;">
    <div style="margin-bottom:8px;color:#6b6b6b;font-size:11px;">${formatAxisTime(axisValue)}</div>
    ${items}
    ${contextRows ? `<div style="display:grid;gap:4px;margin-top:8px;">${contextRows}</div>` : ''}
  </div>`
}

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
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
        bottom: 4,
        height: 16,
        borderColor: 'transparent'
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
          color: '#1976d2'
        },
        areaStyle: {
          color: 'rgba(25, 118, 210, 0.10)'
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
          color: '#9e9e9e'
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
  border-radius: var(--radius-lg);
  padding: 0;
}

.chart-canvas {
  width: 100%;
  height: 520px;
}

@media (max-width: 768px) {
  .chart-canvas {
    height: 400px;
  }
}
</style>
