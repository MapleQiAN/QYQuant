<template>
  <span class="metric-tooltip" @mouseleave="hideTooltip">
    <button
      class="metric-trigger"
      type="button"
      :aria-label="entry?.question || '指标说明'"
      data-test="metric-tooltip-trigger"
      @mouseenter="showTooltip"
      @focus="showTooltip"
      @blur="hideTooltip"
      @click="toggleTooltip"
    >
      ?
    </button>
    <div v-if="open && entry" class="metric-bubble" role="tooltip">
      <strong class="metric-title">{{ entry.question }}</strong>
      <p class="metric-copy">{{ entry.answer }}</p>
    </div>
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { findHelpEntryByMetricKey } from '../../data/help-content'

const props = defineProps<{
  metricKey: string
}>()

const open = ref(false)
const entry = computed(() => findHelpEntryByMetricKey(props.metricKey))

function showTooltip() {
  if (!entry.value) return
  open.value = true
}

function hideTooltip() {
  open.value = false
}

function toggleTooltip() {
  if (!entry.value) return
  open.value = !open.value
}
</script>

<style scoped>
.metric-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
}

.metric-trigger {
  width: 20px;
  height: 20px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 12px;
  cursor: help;
}

.metric-bubble {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  z-index: 220;
  width: min(280px, 70vw);
  padding: 12px 14px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
  transform: translateX(-50%);
}

.metric-title {
  display: block;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.metric-copy {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.5;
}
</style>
