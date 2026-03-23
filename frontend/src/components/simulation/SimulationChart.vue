<template>
  <div class="sim-chart">
    <div v-if="records.length === 0" class="sim-chart__empty">暂无收益曲线数据</div>
    <div ref="chartRef" class="sim-chart__canvas" :class="{ 'sim-chart__canvas--hidden': records.length === 0 }"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import type { SimulationRecord } from '../../types/Simulation'

const props = defineProps<{ records: SimulationRecord[] }>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

function buildOption(): EChartsOption {
  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }),
    },
    grid: {
      left: '4%',
      right: '4%',
      top: 24,
      bottom: 48,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: props.records.map((record) => record.trade_date),
      axisLabel: {
        rotate: 30,
      },
    },
    yAxis: {
      type: 'value',
      name: '权益',
      scale: true,
    },
    series: [
      {
        name: '模拟收益',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#0f766e',
        },
        areaStyle: {
          color: 'rgba(15, 118, 110, 0.10)',
        },
        data: props.records.map((record) => Number(record.equity)),
      },
    ],
  }
}

function renderChart() {
  if (!chart || props.records.length === 0) {
    return
  }
  chart.setOption(buildOption(), true)
}

onMounted(() => {
  if (!chartRef.value) {
    return
  }

  chart = echarts.init(chartRef.value)
  renderChart()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => props.records, () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.sim-chart {
  position: relative;
  min-height: 320px;
}

.sim-chart__empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 14px;
  border: 1px dashed rgba(148, 163, 184, 0.5);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.9);
}

.sim-chart__canvas {
  width: 100%;
  height: 320px;
}

.sim-chart__canvas--hidden {
  visibility: hidden;
}
</style>
