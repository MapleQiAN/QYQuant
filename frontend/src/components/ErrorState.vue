<template>
  <div class="state-card error">
    <div class="state-icon">
      <AlertIcon />
    </div>
    <div class="state-text">
      <h4 class="state-title">{{ titleText }}</h4>
      <p class="state-message">{{ messageText }}</p>
      <button
        v-if="actionLabelText"
        class="state-action"
        type="button"
        @click="$emit('retry')"
      >
        {{ actionLabelText }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'

defineEmits<{ (event: 'retry'): void }>()

const props = defineProps<{
  title?: string
  message?: string
  actionLabel?: string
}>()

const { t } = useI18n()

const titleText = computed(() => props.title || t('states.errorTitle'))
const messageText = computed(() => props.message || '')
const actionLabelText = computed(() => props.actionLabel || '')

const AlertIcon = () => h('svg', {
  width: 24,
  height: 24,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('line', { x1: 12, y1: 8, x2: 12, y2: 12 }),
  h('line', { x1: 12, y1: 16, x2: 12.01, y2: 16 })
])
</script>

<style scoped>
.state-card {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.state-card.error {
  border-color: var(--color-danger);
}

.state-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-danger-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-danger);
  flex-shrink: 0;
}

.state-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.state-message {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.state-action {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-xs);
  border-radius: var(--radius-sm);
  border: none;
  background: var(--color-danger);
  color: var(--color-text-inverse);
  cursor: pointer;
}
</style>
