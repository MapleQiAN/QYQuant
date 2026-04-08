<template>
  <div class="equity-chart">
    <div class="chart-meta">
      <div>
        <h3 class="chart-title">Equity Curve</h3>
        <p class="chart-caption">支持缩放、悬停查看数值与买卖点标注</p>
      </div>
    </div>
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

const tradeMarkers = computed(() => {
  const pointMap = new Map(props.points.map((point) => [point.timestamp, point.equity]))
  return (props.trades || []).map((trade) => {
    const timestamp = Number(trade.timestamp)
    return {
      name: trade.side === 'buy' ? 'Buy' : 'Sell',
      coord: [timestamp, pointMap.get(timestamp) ?? props.points[0]?.equity ?? 0],
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
        valueFormatter: (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
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
      valueFormatter: (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
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
  height: 480px;
}

@media (max-width: 768px) {
  .chart-canvas {
    height: 380px;
  }
}
</style>
