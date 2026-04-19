<template>
  <section class="panel" data-test="alerts-panel">
    <div class="panel__header">
      <span class="panel__eyebrow">AI Alerts</span>
      <h3 class="panel__title">异常提示</h3>
    </div>
    <div class="alerts-grid">
      <article v-for="(item, index) in anomalies" :key="alertKey(item, index)" class="alert-card">
        <strong>{{ item.title || `Alert ${index + 1}` }}</strong>
        <p>{{ stringify(item) }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  anomalies: Array<Record<string, unknown>>
}>()

function stringify(value: Record<string, unknown>): string {
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function alertKey(value: Record<string, unknown>, index: number): string {
  return typeof value.title === 'string' ? value.title : String(index)
}
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
  color: var(--color-warning);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel__title {
  margin: 0;
}

.alerts-grid {
  display: grid;
  gap: var(--spacing-sm);
}

.alert-card {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  background: color-mix(in srgb, var(--color-warning) 6%, var(--color-surface));
}

.alert-card p {
  margin: 0;
  color: var(--color-text-secondary);
}
</style>
