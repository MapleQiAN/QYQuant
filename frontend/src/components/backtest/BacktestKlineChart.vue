<template>
  <div class="kline-chart">
    <div class="kline-chart__status">
      <span class="kline-chart__status-pill">{{ t('backtestReport.tradeSignalsSubtitle') }}</span>
      <span class="kline-chart__status-note">{{ t('backtestReport.hoverInspectorSubtitle') }}</span>
    </div>
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { mapTradeSignalsToBars, simpleMovingAverage, toEpochMs, type TradeMarker } from '../../lib/chartIndicators'
import type { KlineBar } from '../../types/KlineBar'
import type { Trade } from '../../types/Trade'

interface ChartHoverPayload {
  time: string | number
  formattedTime: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  priceChange: number
  signalCount: number
  signals: TradeMarker[]
}

const props = withDefaults(defineProps<{
  bars: KlineBar[]
  trades?: Trade[]
  symbol?: string
}>(), {
  trades: () => [],
  symbol: ''
})

const emit = defineEmits<{
  (event: 'hover-change', payload: ChartHoverPayload | null): void
}>()

const chartRef = ref<HTMLDivElement | null>(null)
const chart = ref<ECharts | null>(null)
let resizeObserver: ResizeObserver | null = null
const { t, locale } = useI18n()

const enrichedBars = computed(() => mapTradeSignalsToBars(props.bars, props.trades))
const categories = computed(() => enrichedBars.value.map((bar) => bar.time))
const candleSeriesName = computed(() => t('kline.candles'))
const volumeSeriesName = computed(() => t('kline.volume'))
const buySeriesName = computed(() => t('kline.buySignal'))
const sellSeriesName = computed(() => t('kline.sellSignal'))

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

function formatNumber(value: number, digits = 4): string {
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

function formatSignedNumber(value: number, digits = 2): string {
  if (!Number.isFinite(value)) {
    return '--'
  }
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${formatNumber(value, digits)}`
}

function buildScatterSeries(side: Trade['side']) {
  const isBuy = side === 'buy'
  const name = isBuy ? buySeriesName.value : sellSeriesName.value
  const accent = isBuy ? '#22c55e' : '#f87171'
  const symbol = isBuy ? 'circle' : 'diamond'

  return enrichedBars.value.flatMap((bar) =>
    (bar.signals ?? [])
      .filter((signal) => signal.side === side)
      .map((signal) => ({
        name,
        value: [signal.barTime, signal.price],
        marker: signal,
        symbol,
        symbolSize: 14,
        itemStyle: {
          color: accent,
          borderColor: '#0b1020',
          borderWidth: 2,
          shadowBlur: 14,
          shadowColor: isBuy ? 'rgba(34, 197, 94, 0.3)' : 'rgba(248, 113, 113, 0.28)',
        },
        label: {
          show: true,
          formatter: isBuy ? 'B' : 'S',
          position: isBuy ? 'top' : 'bottom',
          distance: 8,
          color: accent,
          fontWeight: 800,
          fontSize: 11,
        },
      })),
  )
}

function buildTooltip(params: any[]) {
  if (!Array.isArray(params) || params.length === 0) {
    return ''
  }

  const candle = params.find((item) => item.seriesName === candleSeriesName.value)
  const volume = params.find((item) => item.seriesName === volumeSeriesName.value)
  const maItems = params.filter((item) => String(item.seriesName).startsWith('MA'))
  const tradeItems = params.filter(
    (item) => item.seriesName === buySeriesName.value || item.seriesName === sellSeriesName.value,
  )
  const time = formatTime(candle?.axisValue ?? params[0]?.axisValue)

  let ohlc = ''
  if (candle && Array.isArray(candle.data)) {
    const [open, close, low, high] = candle.data as number[]
    ohlc = `
      <div style="display:grid;grid-template-columns:auto auto;gap:4px 12px;margin-top:8px;">
        <span style="color:#8888a0;">${t('backtestReport.openLabel')}</span><strong>${formatNumber(open)}</strong>
        <span style="color:#8888a0;">${t('backtestReport.highLabel')}</span><strong>${formatNumber(high)}</strong>
        <span style="color:#8888a0;">${t('backtestReport.lowLabel')}</span><strong>${formatNumber(low)}</strong>
        <span style="color:#8888a0;">${t('backtestReport.closeLabel')}</span><strong>${formatNumber(close)}</strong>
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
      <span style="color:${volume.color};">${t('backtestReport.volumeLabel')}</span>
      <strong>${formatNumber(Number(volume.data), 0)}</strong>
    </div>`
    : ''

  const tradeRows = tradeItems
    .map((item) => {
      const marker = item.data?.marker as TradeMarker | undefined
      if (!marker) {
        return ''
      }

      const pnlRow =
        typeof marker.pnl === 'number'
          ? `<div style="display:flex;justify-content:space-between;gap:12px;">
              <span style="color:#8888a0;">${t('backtestReport.tradePnlLabel')}</span>
              <strong>${formatSignedNumber(marker.pnl, 2)}</strong>
            </div>`
          : ''

      return `<div style="padding:8px 10px;border:1px solid rgba(255,255,255,0.08);border-radius:12px;background:rgba(255,255,255,0.03);">
        <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:6px;">
          <strong style="color:${item.color};">${item.seriesName}</strong>
          <span style="color:#8888a0;font-size:11px;">${formatTime(marker.timestamp)}</span>
        </div>
        <div style="display:grid;grid-template-columns:auto auto;gap:4px 12px;">
          <span style="color:#8888a0;">${t('backtestReport.tradePriceLabel')}</span><strong>${formatNumber(marker.price)}</strong>
          <span style="color:#8888a0;">${t('backtestReport.tradeQuantityLabel')}</span><strong>${formatNumber(marker.quantity, 4)}</strong>
        </div>
        ${pnlRow}
      </div>`
    })
    .join('')

  const tradeBlock = tradeRows
    ? `<div style="display:grid;gap:8px;margin-top:10px;">
        <div style="color:#8888a0;font-size:11px;">${t('backtestReport.tradeSignalsTitle')}</div>
        ${tradeRows}
      </div>`
    : ''

  return `<div style="min-width:220px;">
    <div style="margin-bottom:6px;color:#8888a0;font-size:11px;">${time}</div>
    ${ohlc}
    <div style="display:grid;gap:4px;margin-top:8px;">${movingAverages}</div>
    ${volumeRow}
    ${tradeBlock}
  </div>`
}

function buildHoverPayload(dataIndex: number): ChartHoverPayload | null {
  const bar = enrichedBars.value[dataIndex]
  if (!bar) {
    return null
  }

  const priceChange = bar.open !== 0 ? ((bar.close - bar.open) / bar.open) * 100 : 0

  return {
    time: bar.time,
    formattedTime: formatTime(bar.time),
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
    priceChange,
    signalCount: bar.signals?.length ?? 0,
    signals: [...(bar.signals ?? [])],
  }
}

function emitHoverPayload(dataIndex: number) {
  emit('hover-change', buildHoverPayload(dataIndex))
}

function buildOption(): EChartsOption {
  if (!enrichedBars.value.length) {
    return {
      title: {
        text: t('kline.noData'),
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
  const buyMarkers = buildScatterSeries('buy')
  const sellMarkers = buildScatterSeries('sell')

  return {
    animation: false,
    legend: {
      top: 4,
      data: [candleSeriesName.value, 'MA5', 'MA10', 'MA20', volumeSeriesName.value, buySeriesName.value, sellSeriesName.value],
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
        name: candleSeriesName.value,
        type: 'candlestick',
        barMinWidth: 2,
        barMaxWidth: 18,
        data: enrichedBars.value.map((bar) => [bar.open, bar.close, bar.low, bar.high]),
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
        name: volumeSeriesName.value,
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
      },
      {
        name: buySeriesName.value,
        type: 'scatter',
        data: buyMarkers,
        z: 6,
      },
      {
        name: sellSeriesName.value,
        type: 'scatter',
        data: sellMarkers,
        z: 6,
      }
    ]
  }
}

function renderChart() {
  if (!chart.value) return
  chart.value.setOption(buildOption(), true)
  emitHoverPayload(Math.max(enrichedBars.value.length - 1, 0))
}

function handleAxisPointerUpdate(event: any) {
  const axisValue = event?.axesInfo?.[0]?.value
  if (axisValue === undefined || axisValue === null) {
    return
  }

  const dataIndex =
    typeof axisValue === 'number'
      ? axisValue
      : categories.value.findIndex((item) => item === axisValue)

  if (dataIndex >= 0) {
    emitHoverPayload(dataIndex)
  }
}

onMounted(() => {
  if (!chartRef.value) return
  chart.value = echarts.init(chartRef.value)
  chart.value.on('updateAxisPointer', handleAxisPointerUpdate)
  chart.value.on('globalout', () => emitHoverPayload(Math.max(enrichedBars.value.length - 1, 0)))
  renderChart()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart.value?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => [props.bars, props.trades, locale.value], () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart.value?.off('updateAxisPointer', handleAxisPointerUpdate)
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
  padding: 10px 10px 0;
}

.kline-chart__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 6px 10px;
  flex-wrap: wrap;
}

.kline-chart__status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.kline-chart__status-note {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
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
