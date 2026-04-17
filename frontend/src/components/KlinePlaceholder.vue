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
import * as echarts from 'echarts'
import type { ECharts as EChartsInstance, EChartsOption } from 'echarts'
import { buildPositionedTradeMarkers, mapTradeSignalsToBars, simpleMovingAverage, toEpochMs } from '../lib/chartIndicators'
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
  (event: 'timeframe-change', value: string): void
}>()

const { t, locale } = useI18n()
const chartRef = ref<HTMLDivElement | null>(null)

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
const tradeMarkers = computed(() => buildPositionedTradeMarkers(props.data, props.trades))

const upColor = () => getCssVar('--color-up', '#ef4444')
const downColor = () => getCssVar('--color-down', '#10b981')

const formatTime = (value: string | number, tf: string) => {
  const epoch = toEpochMs(value)
  if (epoch === null) return String(value)
  const date = new Date(epoch)
  if (Number.isNaN(date.getTime())) return String(value)

  const lower = tf.toLowerCase()
  if (lower.endsWith('d')) {
    return date.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' })
  }
  if (lower.endsWith('h')) {
    return date.toLocaleString(undefined, { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit' })
  }
  return date.toLocaleString(undefined, { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const getCssVar = (name: string, fallback: string) => {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const formatNumber = (value: number, digits = 4): string => {
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

const formatSignedNumber = (value: number, digits = 2): string => {
  if (!Number.isFinite(value)) return '--'
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${formatNumber(value, digits)}`
}

function buildTooltip(params: any[]) {
  if (!Array.isArray(params) || params.length === 0) return ''

  const candle = params.find((item: any) => item.seriesName === t('kline.candles'))
  const volume = params.find((item: any) => item.seriesName === t('kline.volume'))
  const maItems = params.filter((item: any) => String(item.seriesName).startsWith('MA'))
  const tradeItems = params.filter(
    (item: any) => item.seriesName === t('kline.buySignal') || item.seriesName === t('kline.sellSignal'),
  )
  const time = formatTime(candle?.axisValue ?? params[0]?.axisValue, props.timeframe)

  let ohlc = ''
  if (candle) {
    const idx = candle.dataIndex as number
    const bar = bars.value[idx]
    if (!bar) return ''
    const { open, high, low, close } = bar
    const prevClose = idx > 0 ? bars.value[idx - 1]?.close ?? open : open
    const change = prevClose !== 0 ? ((close - prevClose) / prevClose) * 100 : 0
    const amplitude = prevClose !== 0 ? Math.abs((high - low) / prevClose) * 100 : 0
    const changeColor = change >= 0 ? upColor() : downColor()
    ohlc = `
      <div style="display:grid;grid-template-columns:auto auto;gap:4px 16px;margin-top:10px;font-family:'DM Sans','Noto Sans SC',sans-serif;">
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.openLabel')}</span><strong style="color:#111;font-size:12px;">${formatNumber(open)}</strong>
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.highLabel')}</span><strong style="color:#111;font-size:12px;">${formatNumber(high)}</strong>
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.lowLabel')}</span><strong style="color:#111;font-size:12px;">${formatNumber(low)}</strong>
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.closeLabel')}</span><strong style="color:#111;font-size:12px;">${formatNumber(close)}</strong>
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.changeLabel')}</span><strong style="color:${changeColor};font-size:12px;">${formatSignedNumber(change, 2)}%</strong>
        <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.amplitudeLabel')}</span><strong style="color:#111;font-size:12px;">${formatNumber(amplitude, 2)}%</strong>
      </div>
    `
  }

  const movingAverages = maItems
    .map((item: any) => `<div style="display:flex;justify-content:space-between;gap:16px;font-family:'DM Sans','Noto Sans SC',sans-serif;">
      <span style="color:${item.color};font-size:12px;font-weight:600;">${item.seriesName}</span>
      <strong style="color:#111;font-size:12px;">${Number(item.data).toLocaleString(undefined, { maximumFractionDigits: 4 })}</strong>
    </div>`)
    .join('')

  const volumeRow = volume
    ? `<div style="display:flex;justify-content:space-between;gap:16px;margin-top:10px;font-family:'DM Sans','Noto Sans SC',sans-serif;">
      <span style="color:#8a8a8a;font-size:12px;">${t('backtestReport.volumeLabel')}</span>
      <strong style="color:#111;font-size:12px;">${formatNumber(Number(volume.data), 0)}</strong>
    </div>`
    : ''

  const tradeRows = tradeItems
    .map((item: any) => {
      const marker = item.data?.marker
      if (!marker) return ''
      return `<div style="display:flex;justify-content:space-between;gap:16px;font-family:'DM Sans','Noto Sans SC',sans-serif;">
        <strong style="color:${item.color};font-size:12px;">${item.seriesName}</strong>
        <strong style="color:#111;font-size:12px;">${formatNumber(marker.price)}</strong>
      </div>`
    })
    .join('')

  const tradeBlock = tradeRows
    ? `<div style="display:grid;gap:4px;margin-top:10px;padding-top:8px;border-top:1px solid #e0e0dc;">${tradeRows}</div>`
    : ''

  return `<div style="min-width:240px;font-family:'DM Sans','Noto Sans SC',sans-serif;">
    <div style="margin-bottom:4px;color:#111;font-size:14px;font-weight:700;">${time}</div>
    ${ohlc}
    <div style="display:grid;gap:4px;margin-top:10px;padding-top:8px;border-top:1px solid #e0e0dc;">${movingAverages}</div>
    ${volumeRow}
    ${tradeBlock}
  </div>`
}

const buildSignalSeries = (side: Trade['side']) => {
  const isBuy = side === 'buy'
  const name = isBuy ? t('kline.buySignal') : t('kline.sellSignal')
  const accent = isBuy ? getCssVar('--color-primary', '#1976d2') : getCssVar('--color-accent', '#f9a825')
  const shadowCol = isBuy
    ? 'rgba(25, 118, 210, 0.24)'
    : 'rgba(249, 168, 37, 0.24)'

  return tradeMarkers.value
    .filter((marker) => marker.side === side)
    .flatMap((marker) => {
      const bar = bars.value[marker.barIndex]
      if (!bar) {
        return []
      }

      const anchorPrice = isBuy ? bar.low : bar.high

      return [{
        name,
        // Use barIndex for category-axis lookup; raw barTime breaks scatter on numeric categories.
        value: [marker.barIndex, anchorPrice],
        marker,
        symbol: 'triangle',
        symbolOffset: marker.symbolOffset,
        symbolRotate: isBuy ? 180 : 0,
        symbolSize: 14,
        itemStyle: {
          color: accent,
          borderColor: '#1a1a1a',
          borderWidth: 1.5,
          shadowBlur: 8,
          shadowColor: shadowCol,
        },
        label: {
          show: true,
          formatter: isBuy ? 'B' : 'S',
          position: isBuy ? 'bottom' as const : 'top' as const,
          distance: 3,
          color: accent,
          fontWeight: 700,
          fontSize: 10,
        },
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

  const categories = bars.value.map((bar) => bar.time)
  const closes = bars.value.map((bar) => bar.close)
  const ma5 = simpleMovingAverage(closes, 5)
  const ma10 = simpleMovingAverage(closes, 10)
  const ma20 = simpleMovingAverage(closes, 20)
  const ma30 = simpleMovingAverage(closes, 30)
  const ma60 = simpleMovingAverage(closes, 60)
  const ma120 = simpleMovingAverage(closes, 120)
  const buySignals = buildSignalSeries('buy')
  const sellSignals = buildSignalSeries('sell')

  return {
    animation: false,
    legend: {
      top: 4,
      data: [t('kline.candles'), 'MA5', 'MA10', 'MA20', 'MA30', 'MA60', 'MA120', t('kline.volume'), t('kline.buySignal'), t('kline.sellSignal')],
      textStyle: { color: getCssVar('--color-text-secondary', '#64748b') }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      appendToBody: true,
      backgroundColor: '#ffffff',
      borderColor: '#1a1a1a',
      borderWidth: 2,
      padding: [12, 14],
      textStyle: {
        color: '#111111',
        fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
        fontSize: 12,
      },
      extraCssText: 'border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.07);',
      formatter: (params: any[]) => buildTooltip(params)
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
        boundaryGap: false,
        axisLine: { lineStyle: { color: getCssVar('--color-border', '#e2e8f0') } },
        axisLabel: {
          color: getCssVar('--color-text-muted', '#94a3b8'),
          formatter: (value: string | number) => formatTime(value, props.timeframe),
        },
        axisPointer: {
          label: {
            formatter: (params: any) => formatTime(params.value, props.timeframe)
          }
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
        axisLabel: {
          color: getCssVar('--color-text-muted', '#94a3b8'),
          formatter: (value: string | number) => formatTime(value, props.timeframe),
        },
        axisPointer: {
          label: {
            formatter: (params: any) => formatTime(params.value, props.timeframe)
          }
        }
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
        textStyle: { color: getCssVar('--color-text-muted', '#94a3b8') },
        labelFormatter: (value: string | number) => formatTime(value, props.timeframe)
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
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b' }
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#3b82f6' },
        itemStyle: { color: '#3b82f6' }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#8b5cf6' },
        itemStyle: { color: '#8b5cf6' }
      },
      {
        name: 'MA30',
        type: 'line',
        data: ma30,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#ec4899' },
        itemStyle: { color: '#ec4899' }
      },
      {
        name: 'MA60',
        type: 'line',
        data: ma60,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#14b8a6' },
        itemStyle: { color: '#14b8a6' }
      },
      {
        name: 'MA120',
        type: 'line',
        data: ma120,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#f97316' },
        itemStyle: { color: '#f97316' }
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
      },
      {
        name: t('kline.buySignal'),
        type: 'scatter',
        data: buySignals as any,
        z: 6,
        itemStyle: { color: getCssVar('--color-primary', '#1976d2') },
      },
      {
        name: t('kline.sellSignal'),
        type: 'scatter',
        data: sellSignals as any,
        z: 6,
        itemStyle: { color: getCssVar('--color-accent', '#f9a825') },
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
  emit('timeframe-change', next)
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
