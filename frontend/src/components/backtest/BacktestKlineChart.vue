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
  const includeTime =
    date.getHours() !== 0 ||
    date.getMinutes() !== 0 ||
    date.getSeconds() !== 0

  return date.toLocaleString(undefined, includeTime
    ? { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }
    : { month: '2-digit', day: '2-digit' })
}

function buildMarkPoints() {
  return enrichedBars.value.flatMap((bar) => {
    if (!bar.signal) return []
    const isBuy = bar.signal === 'buy'
    return [{
      name: isBuy ? 'Buy' : 'Sell',
      coord: [bar.time, isBuy ? bar.low : bar.high],
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

function buildTooltip(params: any[]) {
  if (!Array.isArray(params) || params.length === 0) {
    return ''
  }

  const candle = params.find((item) => item.seriesName === 'K线')
  const volume = params.find((item) => item.seriesName === '成交量')
  const maItems = params.filter((item) => String(item.seriesName).startsWith('MA'))
  const time = formatTime(candle?.axisValue ?? params[0]?.axisValue)

  let ohlc = ''
  if (candle && Array.isArray(candle.data)) {
    const [open, close, low, high] = candle.data as number[]
    ohlc = `
      <div style="display:grid;grid-template-columns:auto auto;gap:4px 12px;margin-top:8px;">
        <span style="color:#8888a0;">Open</span><strong>${open.toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
        <span style="color:#8888a0;">High</span><strong>${high.toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
        <span style="color:#8888a0;">Low</span><strong>${low.toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
        <span style="color:#8888a0;">Close</span><strong>${close.toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
      </div>
    `
  }

  const movingAverages = maItems
    .map((item) => `<div style="display:flex;justify-content:space-between;gap:12px;">
      <span style="color:${item.color};">${item.seriesName}</span>
      <strong>${Number(item.data).toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
    </div>`)
    .join('')

  const volumeRow = volume
    ? `<div style="display:flex;justify-content:space-between;gap:12px;margin-top:8px;">
      <span style="color:${volume.color};">Volume</span>
      <strong>${Number(volume.data).toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong>
    </div>`
    : ''

  return `<div style="min-width:220px;">
    <div style="margin-bottom:6px;color:#8888a0;font-size:11px;">${time}</div>
    ${ohlc}
    <div style="display:grid;gap:4px;margin-top:8px;">${movingAverages}</div>
    ${volumeRow}
  </div>`
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

  const categories = enrichedBars.value.map((bar) => bar.time)
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
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(12, 12, 29, 0.94)',
      borderColor: 'rgba(255, 255, 255, 0.08)',
      textStyle: { color: '#ebebf5' },
      formatter: (params) => buildTooltip(params as any[])
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
        axisLabel: {
          color: getCssVar('--color-text-muted', '#94a3b8'),
          fontSize: 10,
          hideOverlap: true,
          formatter: (value: string | number) => formatTime(value)
        },
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
  border-radius: var(--radius-lg);
  background:
    radial-gradient(circle at top left, rgba(124, 109, 216, 0.08), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent);
  padding: 0;
}

.chart-canvas {
  width: 100%;
  height: 460px;
}

@media (max-width: 768px) {
  .chart-canvas {
    height: 360px;
  }
}
</style>
