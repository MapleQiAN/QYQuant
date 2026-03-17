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
          class="tooltip-indicator"
          :data-test="`parameter-${definition.name}-tooltip`"
          :title="definition.description || ''"
        >
          ?
        </span>
      </div>

      <input
        v-if="showSlider(definition)"
        :id="`parameter-${definition.name}`"
        :data-test="`parameter-${definition.name}-slider`"
        class="field-input"
        :class="{ invalid: Boolean(errors[definition.name]) }"
        type="range"
        :disabled="disabled"
        :min="definition.min ?? undefined"
        :max="definition.max ?? undefined"
        :step="definition.step ?? 1"
        :value="String(readValue(definition))"
        @input="updateNumericValue(definition, ($event.target as HTMLInputElement).value)"
      />

      <div v-if="showSlider(definition)" class="slider-value">{{ readValue(definition) }}</div>

      <select
        v-else-if="definition.type === 'enum'"
        :id="`parameter-${definition.name}`"
        :data-test="`parameter-${definition.name}-select`"
        class="field-input"
        :class="{ invalid: Boolean(errors[definition.name]) }"
        :disabled="disabled"
        :value="selectedOptionIndex(definition)"
        @change="updateEnumValue(definition, Number(($event.target as HTMLSelectElement).value))"
      >
        <option
          v-for="(option, index) in definition.options || []"
          :key="`${definition.name}-${index}`"
          :value="index"
        >
          {{ String(option) }}
        </option>
      </select>

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

function updateEnumValue(definition: StrategyParameterDefinition, optionIndex: number) {
  const options = definition.options || []
  emit('update:modelValue', {
    ...mergedValues.value,
    [definition.name]: options[optionIndex],
  })
}

function selectedOptionIndex(definition: StrategyParameterDefinition) {
  const options = definition.options || []
  const current = readValue(definition)
  const index = options.findIndex((option) => option === current)
  return String(index >= 0 ? index : 0)
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
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.parameter-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.parameter-label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.tooltip-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  cursor: help;
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field-input.invalid {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.18);
}

.slider-value {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.field-error {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}
</style>
