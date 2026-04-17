<template>
  <span class="metric-tooltip" @mouseleave="scheduleHide">
    <button
      ref="triggerRef"
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
    <Teleport to="body">
      <Transition name="bubble">
        <div
          v-if="open && entry"
          ref="bubbleRef"
          class="metric-bubble"
          role="tooltip"
          :style="bubbleStyle"
          @mouseenter="cancelHide"
          @mouseleave="hideTooltip"
        >
          <strong class="metric-title">{{ entry.question }}</strong>
          <p class="metric-copy">{{ entry.answer }}</p>
        </div>
      </Transition>
    </Teleport>
  </span>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { findHelpEntryByMetricKey } from '../../data/help-content'

const props = defineProps<{
  metricKey: string
}>()

const open = ref(false)
const entry = computed(() => findHelpEntryByMetricKey(props.metricKey))
const triggerRef = ref<HTMLElement | null>(null)
const bubbleRef = ref<HTMLElement | null>(null)
const bubbleStyle = ref<Record<string, string>>({})
let hideTimer: ReturnType<typeof setTimeout> | null = null

function updatePosition() {
  const trigger = triggerRef.value
  if (!trigger) return

  const rect = trigger.getBoundingClientRect()
  const bubbleWidth = 280
  const gap = 8

  let left = rect.left + rect.width / 2 - bubbleWidth / 2
  left = Math.max(8, Math.min(left, window.innerWidth - bubbleWidth - 8))

  bubbleStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + gap}px`,
    left: `${left}px`,
    width: `${Math.min(bubbleWidth, window.innerWidth * 0.7)}px`,
  }
}

function showTooltip() {
  if (!entry.value) return
  cancelHide()
  open.value = true
  void nextTick(() => updatePosition())
}

function hideTooltip() {
  open.value = false
}

function scheduleHide() {
  hideTimer = setTimeout(hideTooltip, 120)
}

function cancelHide() {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

function toggleTooltip() {
  if (!entry.value) return
  open.value = !open.value
  if (open.value) {
    void nextTick(() => updatePosition())
  }
}
</script>

<style>
/* Not scoped — Teleport renders outside component scope */
.metric-bubble {
  z-index: 500;
  padding: 12px 14px;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
  pointer-events: auto;
}

.metric-bubble .metric-title {
  display: block;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.metric-bubble .metric-copy {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

/* ── bubble transition ── */
.bubble-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.bubble-leave-active {
  transition: opacity 0.1s ease;
}

.bubble-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.bubble-leave-to {
  opacity: 0;
}
</style>

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
  transition: border-color 0.15s, color 0.15s;
}

.metric-trigger:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
