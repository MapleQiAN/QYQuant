<template>
  <label
    class="q-checkbox"
    :class="[
      `q-checkbox--${size}`,
      { 'q-checkbox--checked': isChecked, 'q-checkbox--disabled': disabled }
    ]"
  >
    <input
      type="checkbox"
      class="q-checkbox__input"
      :checked="isChecked"
      :disabled="disabled"
      @change="onChange"
    />
    <span class="q-checkbox__box">
      <svg
        class="q-checkbox__check"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="3.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20 6 9 17 4 12" />
      </svg>
    </span>
    <span v-if="label" class="q-checkbox__label">{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: boolean
  checked?: boolean
  disabled?: boolean
  label?: string
  size?: 'sm' | 'md'
}>(), {
  modelValue: undefined,
  checked: undefined,
  disabled: false,
  label: '',
  size: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'change', value: boolean): void
}>()

const isChecked = computed(() => {
  if (props.modelValue !== undefined) return props.modelValue
  if (props.checked !== undefined) return props.checked
  return false
})

function onChange(event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  emit('update:modelValue', checked)
  emit('change', checked)
}
</script>

<style scoped>
.q-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  user-select: none;
  font-family: var(--font-family);
  line-height: 1;
}

.q-checkbox--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Hidden native input ── */
.q-checkbox__input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* ── Custom box ── */
.q-checkbox__box {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid var(--color-border);
  border-radius: 5px;
  background: var(--color-surface);
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.q-checkbox--md .q-checkbox__box {
  width: 20px;
  height: 20px;
}

.q-checkbox--sm .q-checkbox__box {
  width: 16px;
  height: 16px;
}

.q-checkbox:not(.q-checkbox--disabled):hover .q-checkbox__box {
  border-color: var(--color-primary);
}

.q-checkbox__input:focus-visible + .q-checkbox__box {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

/* ── Checkmark ── */
.q-checkbox__check {
  color: #fff;
  opacity: 0;
  transform: scale(0.5);
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast) var(--ease-out-expo);
}

.q-checkbox--checked .q-checkbox__box {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.q-checkbox--checked .q-checkbox__check {
  opacity: 1;
  transform: scale(1);
}

.q-checkbox--sm .q-checkbox__check {
  width: 10px;
  height: 10px;
}

/* ── Label ── */
.q-checkbox__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}

.q-checkbox--checked .q-checkbox__label {
  color: var(--color-text-primary);
}

.q-checkbox:not(.q-checkbox--disabled):hover .q-checkbox__label {
  color: var(--color-text-primary);
}
</style>
