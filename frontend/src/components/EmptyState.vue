<template>
  <div class="state-card">
    <div class="state-icon">
      <BoxIcon />
    </div>
    <div class="state-text">
      <h4 class="state-title">{{ titleText }}</h4>
      <p class="state-message">{{ messageText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  title?: string
  message?: string
}>()

const { t } = useI18n()

const titleText = computed(() => props.title || t('states.emptyTitle'))
const messageText = computed(() => props.message || t('states.emptyMessage'))

const BoxIcon = () => h('svg', {
  width: 24,
  height: 24,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' }),
  h('path', { d: 'M3.27 6.96 12 12.01l8.73-5.05' }),
  h('path', { d: 'M12 22.08V12' })
])
</script>

<style scoped>
.state-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-border);
}

.state-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.state-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.state-message {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
</style>
