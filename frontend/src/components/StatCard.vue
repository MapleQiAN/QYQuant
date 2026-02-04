<template>
  <div :class="['stat-card', variant]">
    <div class="stat-icon" :style="{ background: iconBg }">
      <slot name="icon">
        <DefaultIcon />
      </slot>
    </div>
    <div class="stat-content">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">
        <span :class="['value', { positive: isPositive, negative: isNegative }]">
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

interface Props {
  label: string
  value: number | string
  prefix?: string
  suffix?: string
  change?: number
  subtitle?: string
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  iconBg?: string
  showSign?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  prefix: '',
  suffix: '',
  variant: 'default',
  iconBg: 'var(--color-primary-bg)',
  showSign: false
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
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-fast);
}

.stat-card:hover {
  box-shadow: var(--shadow-sm);
}

.stat-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--color-primary);
  flex-shrink: 0;
}

.stat-card.success .stat-icon {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.stat-card.warning .stat-icon {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.stat-card.danger .stat-icon {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.stat-card.info .stat-icon {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.value.positive {
  color: var(--color-up);
}

.value.negative {
  color: var(--color-down);
}

.change {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.change.positive {
  background: var(--color-up-bg);
  color: var(--color-up);
}

.change.negative {
  background: var(--color-down-bg);
  color: var(--color-down);
}

.stat-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: var(--spacing-xs);
}
</style>
