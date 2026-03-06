<template>
  <div class="kline-chart">
    <div class="kline-header">
      <div class="kline-title">
        <span class="symbol">{{ symbol }}</span>
        <span class="timeframe">{{ timeframe }}</span>
      </div>
      <div class="kline-controls">
        <button
          v-for="tf in timeframes"
          :key="tf.value"
          :class="['tf-btn', { active: tf.value === timeframe }]"
          @click="handleTimeframeChange(tf.value)"
        >
          {{ tf.label }}
        </button>
      </div>
    </div>

    <div class="chart-container" ref="chartRef"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts/core'
import type { ECharts as EChartsInstance, EChartsOption } from 'echarts'
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts'
import {
  AxisPointerComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { mapTradeSignalsToBars, simpleMovingAverage, toEpochMs } from '../lib/chartIndicators'
import type { KlineBar } from '../types/KlineBar'
import type { Trade } from '../types/Trade'

interface Props {
  data: KlineBar[]
  trades?: Trade[]
  symbol?: string
  timeframe?: string
}

const props = withDefaults(defineProps<Props>(), {
  symbol: 'XAUUSD',
  timeframe: '15m',
  trades: () => []
})

const emit = defineEmits<{
  (event: 'change-timeframe', value: string): void
}>()

const { t, locale } = useI18n()
const chartRef = ref<HTMLDivElement | null>(null)

echarts.use([
  AxisPointerComponent,
  BarChart,
  CandlestickChart,
  CanvasRenderer,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  LineChart,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent
])

let chart: EChartsInstance | null = null
let resizeObserver: ResizeObserver | null = null
let onWindowResize: (() => void) | null = null

const timeframes = computed(() => ([
  { value: '1m', label: t('kline.timeframes.1m') },
  { value: '5m', label: t('kline.timeframes.5m') },
  { value: '15m', label: t('kline.timeframes.15m') },
  { value: '1h', label: t('kline.timeframes.1h') },
  { value: '4h', label: t('kline.timeframes.4h') },
  { value: '1d', label: t('kline.timeframes.1d') }
]))

const bars = computed(() => mapTradeSignalsToBars(props.data, props.trades))

const upColor = () => getCssVar('--color-up', '#ef4444')
const downColor = () => getCssVar('--color-down', '#10b981')

const formatTime = (value: string | number, tf: string) => {
  const epoch = toEpochMs(value)
  if (epoch === null) return String(value)
  const date = new Date(epoch)
  if (Number.isNaN(date.getTime())) return String(value)

  const lower = tf.toLowerCase()
  if (lower.endsWith('d')) {
    return date.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
  }
  if (lower.endsWith('h')) {
    return date.toLocaleString(undefined, { month: '2-digit', day: '2-digit', hour: '2-digit' })
  }
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

const getCssVar = (name: string, fallback: string) => {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const buildMarkPoints = () => {
  return bars.value.flatMap((bar, index) => {
    if (!bar.signal) return []
    const category = formatTime(bar.time, props.timeframe)
    const isBuy = bar.signal === 'buy'
    return [{
      name: isBuy ? t('kline.buySignal') : t('kline.sellSignal'),
      coord: [category, isBuy ? bar.low : bar.high],
      value: isBuy ? 'B' : 'S',
      symbol: 'pin',
      symbolSize: 28,
      symbolOffset: [0, isBuy ? 16 : -16],
      itemStyle: { color: isBuy ? upColor() : downColor() },
      label: {
        show: true,
        formatter: isBuy ? 'B' : 'S',
        color: '#ffffff',
        fontWeight: 700,
        fontSize: 10
      },
      barIndex: index
    }]
  })
}

const buildOption = (): EChartsOption => {
  if (!bars.value.length) {
    return {
      title: {
        text: t('kline.noData'),
        left: 'center',
        top: 'middle',
        textStyle: {
          color: getCssVar('--color-text-muted', '#94a3b8'),
          fontSize: 12,
          fontWeight: 500
        }
      }
    }
  }

  const categories = bars.value.map((bar) => formatTime(bar.time, props.timeframe))
  const closes = bars.value.map((bar) => bar.close)
  const ma5 = simpleMovingAverage(closes, 5)
  const ma10 = simpleMovingAverage(closes, 10)
  const ma20 = simpleMovingAverage(closes, 20)

  return {
    animation: false,
    legend: {
      top: 4,
      data: [t('kline.candles'), 'MA5', 'MA10', 'MA20', t('kline.volume')],
      textStyle: { color: getCssVar('--color-text-secondary', '#64748b') }
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
      { left: '6%', right: '3%', top: '67%', height: '17%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: categories,
        scale: true,
        boundaryGap: false,
        axisLine: { lineStyle: { color: getCssVar('--color-border', '#e2e8f0') } },
        axisLabel: { color: getCssVar('--color-text-muted', '#94a3b8') },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categories,
        boundaryGap: false,
        axisLine: { lineStyle: { color: getCssVar('--color-border', '#e2e8f0') } },
        axisLabel: { color: getCssVar('--color-text-muted', '#94a3b8') }
      }
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: getCssVar('--color-border-light', '#f1f5f9') } },
        axisLabel: { color: getCssVar('--color-text-secondary', '#64748b') }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: {
          color: getCssVar('--color-text-secondary', '#64748b'),
          formatter: (value: number) => value.toLocaleString()
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 60,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 4,
        height: 16,
        start: 60,
        end: 100,
        borderColor: 'transparent',
        textStyle: { color: getCssVar('--color-text-muted', '#94a3b8') }
      }
    ],
    series: [
      {
        name: t('kline.candles'),
        type: 'candlestick',
        data: bars.value.map((bar) => [bar.open, bar.close, bar.low, bar.high]),
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
        name: t('kline.volume'),
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: bars.value.map((bar) => bar.volume),
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const bar = bars.value[params.dataIndex]
            if (!bar) return getCssVar('--color-border', '#e2e8f0')
            return bar.close >= bar.open ? upColor() : downColor()
          }
        }
      }
    ]
  }
}

const renderChart = () => {
  if (!chart) return
  chart.setOption(buildOption(), true)
}

const handleTimeframeChange = (next: string) => {
  if (next === props.timeframe) return
  emit('change-timeframe', next)
}

onMounted(() => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  renderChart()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartRef.value)
  } else {
    onWindowResize = () => chart?.resize()
    window.addEventListener('resize', onWindowResize)
  }
})

watch(
  [bars, () => props.timeframe, () => locale.value],
  () => {
    renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null

  if (onWindowResize) {
    window.removeEventListener('resize', onWindowResize)
    onWindowResize = null
  }

  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.kline-chart {
  width: 100%;
}

.kline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
  gap: var(--spacing-md);
}

.kline-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.symbol {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.timeframe {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: var(--color-background);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.kline-controls {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.tf-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tf-btn:hover {
  border-color: var(--color-primary-light);
  color: var(--color-primary);
}

.tf-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.chart-container {
  width: 100%;
  height: 360px;
  background: var(--color-background);
  border-radius: var(--radius-md);
}

@media (max-width: 768px) {
  .kline-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-container {
    height: 320px;
  }
}
</style>
