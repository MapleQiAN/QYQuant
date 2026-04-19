<template>
  <div class="strategy-mode-switch">
    <button
      v-for="mode in modes"
      :key="mode.value"
      :data-test="`mode-${mode.value}`"
      class="mode-btn"
      :class="{ active: modelValue === mode.value }"
      :disabled="disabled"
      @click="$emit('update:modelValue', mode.value)"
    >
      <span class="mode-icon">{{ mode.icon }}</span>
      <span class="mode-label">{{ mode.label }}</span>
      <span class="mode-desc">{{ mode.description }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
export type StrategyMode = 'guided' | 'mixed' | 'expert'

interface ModeOption {
  value: StrategyMode
  label: string
  description: string
  icon: string
}

withDefaults(defineProps<{
  modelValue: StrategyMode
  disabled?: boolean
}>(), {
  disabled: false,
})

defineEmits<{
  (event: 'update:modelValue', value: StrategyMode): void
}>()

const modes: ModeOption[] = [
  { value: 'guided', label: 'Guided', description: 'AI walks you through', icon: '\uD83D\uDCAC' },
  { value: 'mixed', label: 'Mixed', description: 'AI + manual params', icon: '\uD83D\uDD04' },
  { value: 'expert', label: 'Expert', description: 'Direct parameter control', icon: '\u2699\uFE0F' },
]
</script>

<style scoped>
.strategy-mode-switch {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs);
  border-radius: var(--radius-lg);
  border: 2px solid var(--color-border);
  background: var(--color-surface);
}

.mode-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn:hover:not(:disabled) {
  background: var(--color-surface-hover);
}

.mode-btn.active {
  background: var(--color-accent-bg);
  border-color: var(--color-primary-border);
}

.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.mode-label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.mode-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
</style>
