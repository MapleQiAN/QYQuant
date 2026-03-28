<template>
  <span class="disclaimer-tooltip" @mouseleave="hideTooltip">
    <button
      ref="triggerRef"
      :aria-describedby="tooltipId"
      :aria-expanded="open ? 'true' : 'false'"
      aria-label="收益免责声明"
      class="disclaimer-trigger"
      data-test="disclaimer-tooltip-trigger"
      type="button"
      @blur="hideTooltip"
      @click="toggleTooltip"
      @focus="showTooltipImmediately"
      @mouseenter="showTooltipWithDelay"
    >
      <InfoIcon class="disclaimer-icon" />
    </button>

    <span
      :id="tooltipId"
      ref="bubbleRef"
      :aria-hidden="open ? 'false' : 'true'"
      :class="['disclaimer-bubble', { open, 'is-bottom': placement === 'bottom' }]"
      data-test="disclaimer-tooltip-content"
      role="tooltip"
    >
      {{ props.text }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { h, nextTick, onBeforeUnmount, ref } from 'vue'
import { STRATEGY_TOOLTIP_DISCLAIMER } from '../../data/disclaimer-content'

const props = withDefaults(defineProps<{
  text?: string
}>(), {
  text: STRATEGY_TOOLTIP_DISCLAIMER,
})

const tooltipId = `disclaimer-tooltip-${Math.random().toString(36).slice(2, 10)}`
const bubbleRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const open = ref(false)
const placement = ref<'top' | 'bottom'>('top')

let showTimer: number | null = null

const InfoIcon = () =>
  h(
    'svg',
    {
      width: 12,
      height: 12,
      viewBox: '0 0 24 24',
      fill: 'none',
      xmlns: 'http://www.w3.org/2000/svg',
      'aria-hidden': 'true',
    },
    [
      h('circle', {
        cx: 12,
        cy: 12,
        r: 10,
        stroke: 'currentColor',
        'stroke-width': 2,
      }),
      h('path', {
        d: 'M12 11V16',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
      }),
      h('circle', {
        cx: 12,
        cy: 8,
        r: 1.25,
        fill: 'currentColor',
      }),
    ],
  )

function clearShowTimer() {
  if (showTimer !== null) {
    window.clearTimeout(showTimer)
    showTimer = null
  }
}

function showTooltipWithDelay() {
  clearShowTimer()
  showTimer = window.setTimeout(() => {
    void openTooltip()
  }, 300)
}

function showTooltipImmediately() {
  clearShowTimer()
  void openTooltip()
}

async function openTooltip() {
  open.value = true
  await nextTick()
  updatePlacement()
}

function hideTooltip() {
  clearShowTimer()
  open.value = false
}

function toggleTooltip() {
  if (open.value) {
    hideTooltip()
    return
  }

  showTooltipImmediately()
}

function updatePlacement() {
  const bubble = bubbleRef.value
  const trigger = triggerRef.value

  if (!bubble || !trigger) {
    return
  }

  const triggerRect = trigger.getBoundingClientRect()
  const bubbleRect = bubble.getBoundingClientRect()
  placement.value = triggerRect.top >= bubbleRect.height + 12 ? 'top' : 'bottom'
}

onBeforeUnmount(() => {
  clearShowTimer()
})
</script>

<style scoped>
.disclaimer-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.disclaimer-trigger {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-muted);
  cursor: help;
  flex-shrink: 0;
}

.disclaimer-trigger:focus-visible {
  outline: 2px solid #e53935;
  outline-offset: 2px;
}

.disclaimer-icon {
  display: block;
}

.disclaimer-bubble {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  z-index: 220;
  width: min(280px, 70vw);
  min-width: 200px;
  padding: 10px 12px;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%);
  transition: opacity var(--transition-fast), visibility var(--transition-fast);
  visibility: hidden;
}

.disclaimer-bubble.open {
  opacity: 1;
  visibility: visible;
}

.disclaimer-bubble.is-bottom {
  top: calc(100% + 8px);
  bottom: auto;
}
</style>
