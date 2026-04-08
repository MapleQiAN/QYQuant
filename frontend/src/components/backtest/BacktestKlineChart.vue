<template>
  <div class="kline-chart">
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { mapTradeSignalsToBars, simpleMovingAverage, toEpochMs } from '../../lib/chartIndicators'
import type { KlineBar } from '../../types/KlineBar'
import type { Trade } from '../../types/Trade'

const props = withDefaults(defineProps<{
  bars: KlineBar[]
  trades?: Trade[]
  symbol?: string
}>(), {
  trades: () => [],
  symbol: ''
})

const chartRef = ref<HTMLDivElement | null>(null)
const chart = ref<ECharts | null>(null)
let resizeObserver: ResizeObserver | null = null

const enrichedBars = computed(() => mapTradeSignalsToBars(props.bars, props.trades))

const upColor = () => getCssVar('--color-up', '#ef4444')
const downColor = () => getCssVar('--color-down', '#10b981')

function getCssVar(name: string, fallback: string) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

function formatTime(value: string | number): string {
  const epoch = toEpochMs(value)
  if (epoch === null) return String(value)
  const date = new Date(epoch)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
}

function buildMarkPoints() {
  return enrichedBars.value.flatMap((bar) => {
    if (!bar.signal) return []
    const category = formatTime(bar.time)
    const isBuy = bar.signal === 'buy'
    return [{
      name: isBuy ? 'Buy' : 'Sell',
      coord: [category, isBuy ? bar.low : bar.high],
      value: isBuy ? 'B' : 'S',
      symbol: 'pin',
      symbolSize: 28,
      symbolOffset: [0, isBuy ? 16 : -16],
      itemStyle: { color: isBuy ? '#16a34a' : '#dc2626' },
      label: {
        show: true,
        formatter: isBuy ? 'B' : 'S',
        color: '#ffffff',
        fontWeight: 700,
        fontSize: 10
      }
    }]
  })
}

function buildOption(): EChartsOption {
  if (!enrichedBars.value.length) {
    return {
      title: {
        text: '暂无K线数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: getCssVar('--color-text-muted', '#94a3b8'),
          fontSize: 14,
          fontWeight: 500
        }
      }
    }
  }

  const categories = enrichedBars.value.map((bar) => formatTime(bar.time))
  const closes = enrichedBars.value.map((bar) => bar.close)
  const ma5 = simpleMovingAverage(closes, 5)
  const ma10 = simpleMovingAverage(closes, 10)
  const ma20 = simpleMovingAverage(closes, 20)

  return {
    animation: false,
    legend: {
      top: 4,
      data: ['K线', 'MA5', 'MA10', 'MA20', '成交量'],
      textStyle: { color: getCssVar('--color-text-secondary', '#64748b'), fontSize: 11 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },
    grid: [
      { left: '6%', right: '3%', top: 36, height: '54%' },
      { left: '6%', right: '3%', top: '72%', height: '14%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: categories,
        scale: true,
        boundaryGap: false,
        axisLine: { lineStyle: { color: getCssVar('--color-border', '#e2e8f0') } },
        axisLabel: { color: getCssVar('--color-text-muted', '#94a3b8'), fontSize: 10 },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categories,
        boundaryGap: false,
        axisLine: { lineStyle: { color: getCssVar('--color-border', '#e2e8f0') } },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: getCssVar('--color-border-light', '#f1f5f9') } },
        axisLabel: { color: getCssVar('--color-text-secondary', '#64748b'), fontSize: 10 }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: {
          color: getCssVar('--color-text-secondary', '#64748b'),
          fontSize: 10,
          formatter: (value: number) => value.toLocaleString()
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 4,
        height: 16,
        start: 0,
        end: 100,
        borderColor: 'transparent',
        textStyle: { color: getCssVar('--color-text-muted', '#94a3b8') }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: enrichedBars.value.map((bar) => [bar.open, bar.close, bar.low, bar.high]),
        itemStyle: {
          color: upColor(),
          color0: downColor(),
          borderColor: upColor(),
          borderColor0: downColor()
        },
        markPoint: {
          data: buildMarkPoints()
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#f59e0b' }
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#3b82f6' }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#8b5cf6' }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: enrichedBars.value.map((bar) => bar.volume),
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const bar = enrichedBars.value[params.dataIndex]
            if (!bar) return getCssVar('--color-border', '#e2e8f0')
            return bar.close >= bar.open ? upColor() : downColor()
          }
        }
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

watch(() => [props.bars, props.trades], () => {
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
.kline-chart {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, rgba(15, 118, 110, 0.03), var(--color-surface));
  padding: var(--spacing-md);
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
