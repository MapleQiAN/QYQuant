<template>
  <div :class="['stat-card', variant]">
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
        <span v-if="change !== undefined" :class="['change tnum', { positive: change >= 0, negative: change < 0 }]">
          {{ change >= 0 ? '+' : '' }}{{ change.toFixed(1) }}%
        </span>
      </div>
      <div v-if="subtitle" class="stat-subtitle tnum">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-border);
  transition: border-color var(--transition-fast);
}

.stat-card.success { border-left-color: var(--color-success); }
.stat-card.warning { border-left-color: var(--color-warning); }
.stat-card.danger { border-left-color: var(--color-danger); }
.stat-card.info { border-left-color: var(--color-info); }
.stat-card.up { border-left-color: var(--color-up); }
.stat-card.down { border-left-color: var(--color-down); }

.stat-content {
  min-width: 0;
}

.stat-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-2xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 2px;
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
  font-family: var(--font-mono);
  line-height: 1.2;
}

.value.positive {
  color: var(--color-up);
}

.value.negative {
  color: var(--color-down);
}

.change {
  font-size: var(--font-size-2xs);
  font-weight: var(--font-weight-medium);
  padding: 1px 4px;
  border-radius: var(--radius-xs);
  font-family: var(--font-mono);
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
  font-size: var(--font-size-2xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}
</style>
