<template>
  <article class="metric-tile">
    <span class="metric-tile__label">
      {{ label }}
      <MetricTooltip :metric-key="metricKey" />
    </span>
    <strong :class="['metric-tile__value', toneClass]">{{ value }}</strong>
    <span class="metric-tile__caption">{{ caption }}</span>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MetricTooltip from '../../../components/help/MetricTooltip.vue'

const props = defineProps<{
  label: string
  value: string
  caption: string
  tone: string
  metricKey: string
}>()

const toneClass = computed(() => `tone-${props.tone}`)
</script>

<style scoped>
.metric-tile {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.metric-tile__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.metric-tile__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xxl);
  font-weight: 900;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.metric-tile__caption {
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.tone-positive {
  color: var(--color-positive);
}

.tone-negative {
  color: var(--color-negative);
}

.tone-warning {
  color: var(--color-warning);
}

.tone-neutral {
  color: var(--color-text-secondary);
}
</style>
