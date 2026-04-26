<template>
  <div class="parameter-form">
    <article
      v-for="definition in definitions"
      :key="definition.name"
      class="parameter-card"
    >
      <div class="parameter-head">
        <label class="parameter-label" :for="`parameter-${definition.name}`">
          {{ definition.name }}
        </label>
        <span
          v-if="definition.description"
          class="tooltip-trigger"
          :data-test="`parameter-${definition.name}-tooltip`"
          tabindex="0"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span class="tooltip-bubble">{{ definition.description }}</span>
        </span>
      </div>

      <div v-if="showSlider(definition)" class="slider-group">
        <input
          :id="`parameter-${definition.name}`"
          :data-test="`parameter-${definition.name}-slider`"
          class="slider-input"
          :class="{ invalid: Boolean(errors[definition.name]) }"
          type="range"
          :disabled="disabled"
          :min="definition.min ?? undefined"
          :max="definition.max ?? undefined"
          :step="definition.step ?? 1"
          :value="String(readValue(definition))"
          @input="updateNumericValue(definition, ($event.target as HTMLInputElement).value)"
        />
        <div class="slider-info">
          <span class="slider-bound">{{ definition.min }}</span>
          <span class="slider-current">{{ readValue(definition) }}</span>
          <span class="slider-bound">{{ definition.max }}</span>
        </div>
      </div>

      <QSelect
        v-else-if="definition.type === 'enum'"
        :id="`parameter-${definition.name}`"
        :data-test="`parameter-${definition.name}-select`"
        :class="{ invalid: Boolean(errors[definition.name]) }"
        :disabled="disabled"
        :model-value="readValue(definition)"
        :options="enumOptions(definition)"
        @update:model-value="updateEnumValue(definition, $event)"
      />

      <input
        v-else-if="definition.type === 'int' || definition.type === 'float'"
        :id="`parameter-${definition.name}`"
        :data-test="`parameter-${definition.name}-number`"
        class="field-input"
        :class="{ invalid: Boolean(errors[definition.name]) }"
        :disabled="disabled"
        type="number"
        :step="definition.step ?? (definition.type === 'int' ? 1 : 'any')"
        :min="definition.min ?? undefined"
        :max="definition.max ?? undefined"
        :value="String(readValue(definition))"
        @input="updateNumericValue(definition, ($event.target as HTMLInputElement).value)"
      />

      <input
        v-else
        :id="`parameter-${definition.name}`"
        :data-test="`parameter-${definition.name}-text`"
        class="field-input"
        :class="{ invalid: Boolean(errors[definition.name]) }"
        :disabled="disabled"
        type="text"
        :value="String(readValue(definition))"
        @input="updateTextValue(definition, ($event.target as HTMLInputElement).value)"
      />

      <p v-if="errors[definition.name]" class="field-error">{{ errors[definition.name] }}</p>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import type { StrategyParameterDefinition, StrategyParameterValue } from '../../types/Strategy'
import { QSelect } from '../ui'

const props = withDefaults(defineProps<{
  definitions: StrategyParameterDefinition[]
  modelValue: Record<string, unknown>
  disabled?: boolean
}>(), {
  disabled: false,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: Record<string, unknown>): void
  (event: 'validation-change', value: boolean): void
}>()

const mergedValues = computed(() => {
  const next = { ...(props.modelValue || {}) }
  for (const definition of props.definitions) {
    if (next[definition.name] === undefined && definition.default !== undefined) {
      next[definition.name] = definition.default
    }
  }
  return next
})

const errors = computed<Record<string, string>>(() => {
  const next: Record<string, string> = {}
  for (const definition of props.definitions) {
    const message = validateDefinition(definition, mergedValues.value[definition.name])
    if (message) {
      next[definition.name] = message
    }
  }
  return next
})

watch(
  () => props.definitions,
  () => {
    const next = { ...(props.modelValue || {}) }
    let changed = false
    for (const definition of props.definitions) {
      if (next[definition.name] === undefined && definition.default !== undefined) {
        next[definition.name] = definition.default
        changed = true
      }
    }
    if (changed) {
      emit('update:modelValue', next)
    }
  },
  { deep: true, immediate: true },
)

watch(
  errors,
  (value) => {
    emit('validation-change', Object.keys(value).length === 0)
  },
  { deep: true, immediate: true },
)

function showSlider(definition: StrategyParameterDefinition) {
  return (
    (definition.type === 'int' || definition.type === 'float') &&
    definition.min != null &&
    definition.max != null &&
    definition.step != null
  )
}

function readValue(definition: StrategyParameterDefinition) {
  const current = mergedValues.value[definition.name]
  if (current === undefined || current === null) {
    return definition.default ?? ''
  }
  return current
}

function updateNumericValue(definition: StrategyParameterDefinition, rawValue: string) {
  const nextValue = rawValue === '' ? '' : Number(rawValue)
  emit('update:modelValue', {
    ...mergedValues.value,
    [definition.name]: nextValue,
  })
}

function updateTextValue(definition: StrategyParameterDefinition, rawValue: string) {
  emit('update:modelValue', {
    ...mergedValues.value,
    [definition.name]: rawValue,
  })
}

function updateEnumValue(definition: StrategyParameterDefinition, value: unknown) {
  emit('update:modelValue', {
    ...mergedValues.value,
    [definition.name]: value,
  })
}

function enumOptions(definition: StrategyParameterDefinition) {
  return (definition.options || []).map((o) => ({ label: String(o), value: o }))
}

function validateDefinition(definition: StrategyParameterDefinition, value: unknown) {
  if (isEmpty(value)) {
    return definition.required ? 'This field is required' : ''
  }

  if (definition.type === 'int' || definition.type === 'float') {
    const numeric = typeof value === 'number' ? value : Number(value)
    if (Number.isNaN(numeric)) {
      return 'Must be a number'
    }
    if (definition.type === 'int' && !Number.isInteger(numeric)) {
      return 'Must be an integer'
    }
    if (definition.min != null && numeric < definition.min) {
      return `Must be at least ${formatValue(definition.min)}`
    }
    if (definition.max != null && numeric > definition.max) {
      return `Must be at most ${formatValue(definition.max)}`
    }
    return ''
  }

  if (definition.type === 'enum') {
    const options = definition.options || []
    return options.some((option) => option === value) ? '' : 'Please choose a valid option'
  }

  return ''
}

function isEmpty(value: unknown) {
  return value === undefined || value === null || value === ''
}

function formatValue(value: StrategyParameterValue | number) {
  return Number.isInteger(value) ? String(value) : String(Number(value))
}
</script>

<style scoped>
.parameter-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-md);
}

.parameter-card {
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-xs);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.parameter-card:hover {
  box-shadow: var(--shadow-sm);
}

.parameter-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.parameter-label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

/* ── Tooltip ── */
.tooltip-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  cursor: help;
}

.tooltip-bubble {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-active);
  border: 2px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 400;
  line-height: 1.4;
  white-space: normal;
  max-width: 260px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 10;
  box-shadow: var(--shadow-md);
}

.tooltip-bubble::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--color-border);
}

.tooltip-trigger:hover .tooltip-bubble,
.tooltip-trigger:focus .tooltip-bubble {
  opacity: 1;
}

/* ── Field Input ── */
.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px rgba(30, 90, 168, 0.12);
}

.field-input.invalid {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px rgba(212, 57, 59, 0.15);
}

/* ── Slider ── */
.slider-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.slider-input {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: var(--radius-xs);
  background: var(--color-border-light);
  border: 2px solid var(--color-border);
  outline: none;
  cursor: pointer;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: var(--shadow-md);
}

.slider-input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.slider-input.invalid::-webkit-slider-thumb {
  background: var(--color-danger);
  box-shadow: 0 0 0 2px rgba(255, 59, 59, 0.3);
}

.slider-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-bound {
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.slider-current {
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-text-primary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  background: var(--color-accent-bg);
}

.field-error {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}
</style>
