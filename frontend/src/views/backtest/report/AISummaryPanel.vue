<template>
  <section class="panel" data-test="ai-summary-panel">
    <div class="panel__header">
      <span class="panel__eyebrow">AI Summary</span>
      <h3 class="panel__title">{{ $t('backtestReport.executiveSummary') }}</h3>
    </div>
    <p class="panel__body">{{ summary }}</p>
    <div v-if="entries.length" class="narration-grid">
      <article v-for="[key, value] in entries" :key="key" class="narration-row">
        <strong>{{ key }}</strong>
        <p>{{ value }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  summary: string
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
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel__title,
.narration-row p {
  margin: 0;
}

.panel__body {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.narration-grid {
  display: grid;
  gap: var(--spacing-sm);
}

.narration-row {
  padding: 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.narration-row strong {
  display: block;
  margin-bottom: 6px;
}
</style>
