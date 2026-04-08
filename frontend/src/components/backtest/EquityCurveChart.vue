<template>
  <div class="equity-chart">
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
  return (props.trades || []).map((trade) => {
    const timestamp = Number(trade.timestamp)
    const nearestPoint = findNearestPoint(timestamp)
    return {
      name: trade.side === 'buy' ? 'Buy' : 'Sell',
      coord: [nearestPoint?.timestamp ?? timestamp, nearestPoint?.equity ?? props.points[0]?.equity ?? 0],
      value: trade.side === 'buy' ? 'B' : 'S',
      symbol: 'pin',
      symbolSize: 28,
      symbolOffset: [0, trade.side === 'buy' ? 16 : -16],
      itemStyle: {
        color: trade.side === 'buy' ? '#16a34a' : '#dc2626'
      },
      label: {
        show: true,
        color: '#ffffff',
        formatter: trade.side === 'buy' ? 'B' : 'S',
        fontWeight: 700,
        fontSize: 10
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
        <strong style="color:#ebebf5;">${formatTooltipValue(rawValue)}</strong>
      </div>`
    })
    .join('')

  const contextRows = [
    strategyReturn === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#8888a0;">Strategy Return</span>
          <strong style="color:#ebebf5;">${strategyReturn.toFixed(2)}%</strong>
        </div>`,
    benchmarkReturn === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#8888a0;">Benchmark Return</span>
          <strong style="color:#ebebf5;">${benchmarkReturn.toFixed(2)}%</strong>
        </div>`,
    currentPoint?.drawdown === undefined || currentPoint?.drawdown === null
      ? ''
      : `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span style="color:#8888a0;">Drawdown</span>
          <strong style="color:#ebebf5;">${Number(currentPoint.drawdown).toFixed(2)}%</strong>
        </div>`
  ].filter(Boolean).join('')

  return `<div style="min-width:190px;">
    <div style="margin-bottom:8px;color:#8888a0;font-size:11px;">${formatAxisTime(axisValue)}</div>
    ${items}
    ${contextRows ? `<div style="display:grid;gap:4px;margin-top:8px;">${contextRows}</div>` : ''}
  </div>`
}

function buildOption(): EChartsOption {
  if (!props.points.length) {
    return {
      title: {
        text: '暂无权益曲线数据',
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

  const equityData = props.points.map((point) => [point.timestamp, point.equity])
  const benchmarkData = props.points.map((point) => [point.timestamp, point.benchmark_equity])

  if (!hasDrawdown.value) {
    return {
      animation: false,
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(12, 12, 29, 0.92)',
        borderColor: 'rgba(255, 255, 255, 0.08)',
        textStyle: { color: '#ebebf5' },
        formatter: (params) => buildTooltip(params as any[])
      },
      legend: {
        top: 8,
        data: ['策略权益', '基准走势']
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
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', start: 0, end: 100, bottom: 10, height: 18 }
      ],
      series: [
        {
          name: '策略权益',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2, color: '#0f766e' },
          areaStyle: { color: 'rgba(15, 118, 110, 0.10)' },
          data: equityData,
          markPoint: { data: tradeMarkers.value }
        },
        {
          name: '基准走势',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1.5, type: 'dashed', color: '#94a3b8' },
          data: benchmarkData
        }
      ]
    }
  }

  const drawdownData = props.points.map((point) => [point.timestamp, point.drawdown ?? 0])

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(12, 12, 29, 0.92)',
      borderColor: 'rgba(255, 255, 255, 0.08)',
      textStyle: { color: '#ebebf5' },
      formatter: (params) => buildTooltip(params as any[])
    },
    legend: {
      top: 8,
      data: ['策略权益', '基准走势', '回撤']
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },
    grid: [
      { left: '5%', right: '3%', top: 48, height: '50%' },
      { left: '5%', right: '3%', top: '74%', height: '14%' }
    ],
    xAxis: [
      { type: 'time', gridIndex: 0 },
      { type: 'time', gridIndex: 1 }
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.12)' } }
      },
      {
        type: 'value',
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: {
          formatter: (value: number) => `${value.toFixed(1)}%`
        },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      {
        show: true,
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
        name: '策略权益',
        type: 'line',
        smooth: true,
        showSymbol: false,
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { width: 2, color: '#0f766e' },
        areaStyle: { color: 'rgba(15, 118, 110, 0.10)' },
        data: equityData,
        markPoint: { data: tradeMarkers.value }
      },
      {
        name: '基准走势',
        type: 'line',
        smooth: true,
        showSymbol: false,
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { width: 1.5, type: 'dashed', color: '#94a3b8' },
        data: benchmarkData
      },
      {
        name: '回撤',
        type: 'line',
        smooth: true,
        showSymbol: false,
        xAxisIndex: 1,
        yAxisIndex: 1,
        lineStyle: { width: 1, color: '#dc2626' },
        areaStyle: { color: 'rgba(220, 38, 38, 0.18)' },
        data: drawdownData
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

watch(() => [props.points, props.trades], () => {
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
  background:
    radial-gradient(circle at top left, rgba(54, 214, 182, 0.08), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent);
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
