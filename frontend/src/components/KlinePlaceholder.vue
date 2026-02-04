<template>
  <div class="kline-placeholder">
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
        >
          {{ tf.label }}
        </button>
      </div>
    </div>

    <div class="chart-container" ref="chartRef">
      <svg class="chart-svg" :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none">
        <g class="grid-lines">
          <line
            v-for="i in 5"
            :key="'h-' + i"
            :x1="0"
            :y1="(chartHeight / 5) * i"
            :x2="chartWidth"
            :y2="(chartHeight / 5) * i"
            stroke="var(--color-border-light)"
            stroke-dasharray="4,4"
          />
        </g>

        <g class="candles">
          <g v-for="(candle, index) in normalizedData" :key="index">
            <line
              :x1="candle.x + candleWidth / 2"
              :y1="candle.highY"
              :x2="candle.x + candleWidth / 2"
              :y2="candle.lowY"
              :stroke="candle.color"
              stroke-width="1"
            />
            <rect
              :x="candle.x"
              :y="candle.bodyY"
              :width="candleWidth"
              :height="Math.max(candle.bodyHeight, 2)"
              :fill="candle.color"
              rx="2"
            />
            <g v-if="candle.signal">
              <circle
                :cx="candle.x + candleWidth / 2"
                :cy="candle.signal === 'buy' ? candle.lowY + 20 : candle.highY - 20"
                r="8"
                :fill="candle.signal === 'buy' ? 'var(--color-up)' : 'var(--color-down)'"
                opacity="0.2"
              />
              <text
                :x="candle.x + candleWidth / 2"
                :y="candle.signal === 'buy' ? candle.lowY + 24 : candle.highY - 16"
                text-anchor="middle"
                :fill="candle.signal === 'buy' ? 'var(--color-up)' : 'var(--color-down)'"
                font-size="10"
                font-weight="600"
              >
                {{ candle.signal === 'buy' ? 'B' : 'S' }}
              </text>
            </g>
          </g>
        </g>

        <line
          :x1="0"
          :y1="currentPriceY"
          :x2="chartWidth"
          :y2="currentPriceY"
          stroke="var(--color-primary)"
          stroke-width="1"
          stroke-dasharray="6,3"
          opacity="0.6"
        />
      </svg>

      <div class="price-tag" :style="{ top: currentPriceY + 'px' }">
        {{ currentPrice.toFixed(2) }}
      </div>

      <div class="time-axis">
        <span v-for="(time, index) in timeLabels" :key="index" class="time-label">
          {{ time }}
        </span>
      </div>
    </div>

    <div class="chart-legend">
      <div class="legend-item">
        <span class="legend-dot buy"></span>
        <span>{{ $t('kline.buySignal') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot sell"></span>
        <span>{{ $t('kline.sellSignal') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { KlineBar } from '../types/KlineBar'

interface Props {
  data: KlineBar[]
  symbol?: string
  timeframe?: string
}

const props = withDefaults(defineProps<Props>(), {
  symbol: 'XAUUSD',
  timeframe: '15m'
})

defineExpose({
  initChart: (library: 'echarts' | 'lightweight-charts') => {
    console.log(`Ready to initialize ${library} chart`)
  },
  updateData: (newData: KlineBar[]) => {
    console.log('Updating chart data', newData)
  }
})

const { t } = useI18n()

const chartRef = ref<HTMLElement>()
const chartWidth = 800
const chartHeight = 280
const candleWidth = 12
const candleGap = 4

const timeframes = computed(() => ([
  { value: '1m', label: t('kline.timeframes.1m') },
  { value: '5m', label: t('kline.timeframes.5m') },
  { value: '15m', label: t('kline.timeframes.15m') },
  { value: '1h', label: t('kline.timeframes.1h') },
  { value: '4h', label: t('kline.timeframes.4h') },
  { value: '1d', label: t('kline.timeframes.1d') }
]))

const priceRange = computed(() => {
  if (!props.data.length) return { min: 0, max: 0 }
  const prices = props.data.flatMap((d) => [d.high, d.low])
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const padding = (max - min) * 0.1
  return { min: min - padding, max: max + padding }
})

const normalizedData = computed(() => {
  const { min, max } = priceRange.value
  const range = max - min

  return props.data.map((candle, index) => {
    const x = index * (candleWidth + candleGap) + 40
    const openY = chartHeight - ((candle.open - min) / range) * chartHeight
    const closeY = chartHeight - ((candle.close - min) / range) * chartHeight
    const highY = chartHeight - ((candle.high - min) / range) * chartHeight
    const lowY = chartHeight - ((candle.low - min) / range) * chartHeight
    const isUp = candle.close >= candle.open

    return {
      x,
      highY,
      lowY,
      bodyY: Math.min(openY, closeY),
      bodyHeight: Math.abs(closeY - openY),
      color: isUp ? 'var(--color-up)' : 'var(--color-down)',
      signal: candle.signal
    }
  })
})

const currentPrice = computed(() => {
  if (!props.data.length) return 0
  return props.data[props.data.length - 1].close
})

const currentPriceY = computed(() => {
  const { min, max } = priceRange.value
  const range = max - min
  return chartHeight - ((currentPrice.value - min) / range) * chartHeight
})

const parseEpoch = (value: string | number): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    if (value > 1e12) return value
    if (value > 1e9) return value * 1000
    return null
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    if (/^\d+$/.test(trimmed)) {
      const numeric = Number(trimmed)
      if (numeric > 1e12) return numeric
      if (numeric > 1e9) return numeric * 1000
      return null
    }
    if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) {
      const parsed = Date.parse(trimmed)
      return Number.isNaN(parsed) ? null : parsed
    }
  }

  return null
}

const formatTimeLabel = (value: string | number) => {
  const epoch = parseEpoch(value)
  if (epoch === null) return String(value)
  const date = new Date(epoch)
  if (Number.isNaN(date.getTime())) return String(value)
  const tf = (props.timeframe ?? '15m').toLowerCase()
  const showDate = tf.endsWith('d')
  if (showDate) {
    return date.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
  }
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

const timeLabels = computed(() => {
  if (!props.data.length) return []
  const step = Math.ceil(props.data.length / 6)
  return props.data
    .filter((_, index) => index % step === 0)
    .map((d) => formatTimeLabel(d.time))
})
</script>

<style scoped>
.kline-placeholder {
  width: 100%;
}

.kline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
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
  position: relative;
  width: 100%;
  height: 280px;
  background: var(--color-background);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.price-tag {
  position: absolute;
  right: 0;
  transform: translateY(-50%);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
}

.time-axis {
  position: absolute;
  bottom: 0;
  left: 40px;
  right: 60px;
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
}

.time-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.chart-legend {
  display: flex;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.legend-dot.buy {
  background: var(--color-up);
}

.legend-dot.sell {
  background: var(--color-down);
}
</style>
