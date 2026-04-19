<template>
  <section class="panel" data-test="diagnosis-panel">
    <div class="panel__header">
      <span class="panel__eyebrow">{{ $t('backtestReport.diagnosticsTitle') }}</span>
      <h3 class="panel__title">{{ $t('backtestReport.qualityScore') }}</h3>
    </div>
    <p v-if="diagnosis" class="panel__body">{{ diagnosis }}</p>
    <div v-if="entries.length" class="diagnosis-grid">
      <article v-for="[key, value] in entries" :key="key" class="diagnosis-row">
        <strong>{{ key }}</strong>
        <p>{{ value }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  diagnosis?: string
  metricNarrations?: Record<string, string>
}>()

const entries = computed(() => Object.entries(props.metricNarrations ?? {}))
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

.panel__header {
  display: grid;
  gap: 6px;
}

.panel__eyebrow {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel__title,
.panel__body,
.diagnosis-row p {
  margin: 0;
}

.panel__body,
.diagnosis-row p {
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.diagnosis-grid {
  display: grid;
  gap: var(--spacing-sm);
}

.diagnosis-row {
  padding: 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
}

.diagnosis-row strong {
  display: block;
  margin-bottom: 6px;
}
</style>
