<template>
  <section class="panel" data-test="comparison-panel">
    <div class="panel__header">
      <span class="panel__eyebrow">AI Comparison</span>
      <h3 class="panel__title">{{ title }}</h3>
    </div>

    <div v-if="parameterSensitivity.length" class="panel__group">
      <strong class="panel__group-title">Parameter Sensitivity</strong>
      <pre class="panel__code">{{ JSON.stringify(parameterSensitivity, null, 2) }}</pre>
    </div>

    <div v-if="hasMonteCarlo" class="panel__group">
      <strong class="panel__group-title">Monte Carlo</strong>
      <pre class="panel__code">{{ JSON.stringify(monteCarlo, null, 2) }}</pre>
    </div>

    <div v-if="regimeAnalysis.length" class="panel__group">
      <strong class="panel__group-title">Regime Analysis</strong>
      <pre class="panel__code">{{ JSON.stringify(regimeAnalysis, null, 2) }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title?: string
  parameterSensitivity?: Array<Record<string, unknown>>
  monteCarlo?: Record<string, unknown> | null
  regimeAnalysis?: Array<Record<string, unknown>>
}>()

const parameterSensitivity = computed(() => props.parameterSensitivity ?? [])
const regimeAnalysis = computed(() => props.regimeAnalysis ?? [])
const monteCarlo = computed(() => props.monteCarlo ?? null)
const hasMonteCarlo = computed(() => !!monteCarlo.value && Object.keys(monteCarlo.value).length > 0)
const title = computed(() => props.title || '高级诊断对比')
</script>

<style scoped>
.panel {
  display: grid;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.panel__header,
.panel__group {
  display: grid;
  gap: 8px;
}

.panel__eyebrow {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel__title {
  margin: 0;
}

.panel__group-title {
  color: var(--color-text-primary);
}

.panel__code {
  margin: 0;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  overflow: auto;
  font-size: 12px;
}
</style>
