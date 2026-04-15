<template>
  <div class="drawdown-chart">
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import type { BacktestReportPoint } from '../../types/Backtest'

const props = defineProps<{
  points: BacktestReportPoint[]
}>()

const { t, locale } = useI18n()
const chartRef = ref<HTMLDivElement | null>(null)
const chart = ref<ECharts | null>(null)
let resizeObserver: ResizeObserver | null = null

function buildOption(): EChartsOption {
  const drawdownData = props.points
    .filter((p) => p.drawdown !== undefined)
    .map((p) => [p.timestamp, p.drawdown])

  if (!drawdownData.length) {
    return {
      title: {
        text: t('drawdownChart.noData'),
        left: 'center',
        top: 'middle',
        textStyle: { color: '#64748b', fontSize: 14, fontWeight: 500 }
      }
    }
  }

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => Number(value).toFixed(2) + '%'
    },
    grid: {
      left: '5%',
      right: '3%',
      top: 16,
      bottom: 40
    },
    xAxis: {
      type: 'time',
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: '#64748b',
        formatter: (value: number) => value.toFixed(1) + '%'
      },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 }
    ],
    series: [
      {
        name: t('drawdownChart.drawdown'),
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#d4393b' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(212, 57, 59, 0.20)' },
            { offset: 1, color: 'rgba(212, 57, 59, 0.02)' }
          ])
        },
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

watch(() => [props.points, locale.value], () => {
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
.drawdown-chart {
  padding: var(--spacing-sm);
}

.chart-canvas {
  width: 100%;
  height: 200px;
}

@media (max-width: 768px) {
  .chart-canvas {
    height: 160px;
  }
}
</style>
