<template>
  <div :class="['stat-card', variant]">
    <div class="stat-icon" :style="{ background: iconBg }">
      <slot name="icon">
        <DefaultIcon />
      </slot>
    </div>
    <div class="stat-content">
      <div class="stat-label">
        <span>{{ label }}</span>
        <DisclaimerTooltip v-if="showDisclaimer" />
        <slot name="label-extra" />
      </div>
      <div class="stat-value">
        <span :class="['value tnum', { positive: isPositive, negative: isNegative }]">
          {{ prefix }}{{ formattedValue }}{{ suffix }}
        </span>
        <span v-if="change !== undefined" :class="['change', { positive: change >= 0, negative: change < 0 }]">
          {{ change >= 0 ? '+' : '' }}{{ change.toFixed(1) }}%
        </span>
      </div>
      <div v-if="subtitle" class="stat-subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import DisclaimerTooltip from './disclaimer/DisclaimerTooltip.vue'

interface Props {
  label: string
  value: number | string
  prefix?: string
  suffix?: string
  change?: number
  subtitle?: string
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'up' | 'down'
  iconBg?: string
  showSign?: boolean
  showDisclaimer?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  prefix: '',
  suffix: '',
  variant: 'default',
  iconBg: 'var(--color-primary-bg)',
  showSign: false,
  showDisclaimer: false
})

const DefaultIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' })
])

const formattedValue = computed(() => {
  const val = props.value
  if (typeof val === 'string') return val
  if (Math.abs(val) >= 10000) {
    return (val / 10000).toFixed(2) + '万'
  }
  return val.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
})

const isPositive = computed(() => {
  if (!props.showSign) return false
  const val = typeof props.value === 'number' ? props.value : parseFloat(props.value as string)
  return val > 0
})

const isNegative = computed(() => {
  if (!props.showSign) return false
  const val = typeof props.value === 'number' ? props.value : parseFloat(props.value as string)
  return val < 0
})
</script>

<style scoped>
.stat-card {
  display: grid;
  gap: 6px;
  padding: 20px;
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
  border-radius: 0 0 8px 8px;
}

.stat-card.success::after { background: var(--color-success); }
.stat-card.up::after { background: var(--color-up); }
.stat-card.warning::after { background: var(--color-accent); }
.stat-card.danger::after { background: var(--color-danger); }
.stat-card.down::after { background: var(--color-down); }
.stat-card.info::after { background: var(--color-info); }

.stat-icon {
  display: none;
}

.stat-content {
  min-width: 0;
}

.stat-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.value {
  font-size: var(--font-size-xxl);
  font-weight: 900;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.value.positive { color: var(--color-positive); }
.value.negative { color: var(--color-negative); }

.change {
  font-size: var(--font-size-xs);
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  border: 2px solid transparent;
}

.change.positive { background: var(--color-positive-bg); color: var(--color-positive); border-color: var(--color-positive); }
.change.negative { background: var(--color-negative-bg); color: var(--color-negative); border-color: var(--color-negative); }

.stat-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: var(--spacing-xs);
}

@media (max-width: 768px) {
  .stat-card { padding: 14px; }
  .value { font-size: var(--font-size-xl); }
}

@media (max-width: 480px) {
  .stat-card { padding: 12px; }
}
</style>
