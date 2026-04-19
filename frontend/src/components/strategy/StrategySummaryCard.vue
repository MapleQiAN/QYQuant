<template>
  <div v-if="summary" class="strategy-summary-card">
    <div class="summary-header">
      <h3 class="summary-title">Strategy Preview</h3>
      <span v-if="summary.confidence" class="confidence-badge">
        {{ Math.round(summary.confidence * 100) }}% match
      </span>
    </div>

    <p class="summary-text">{{ summary.summary }}</p>
    <p class="summary-explanation">{{ summary.explanation }}</p>

    <div v-if="summary.parameters && summary.parameters.length > 0" class="param-list">
      <h4 class="param-list-title">Parameters</h4>
      <div class="param-grid">
        <div
          v-for="param in summary.parameters"
          :key="param.key"
          class="param-item"
        >
          <span class="param-key">{{ param.label || param.key }}</span>
          <span class="param-purpose">{{ param.purpose }}</span>
        </div>
      </div>
    </div>

    <div class="summary-actions">
      <button class="btn btn-primary" @click="$emit('confirm')">
        Confirm & Run Backtest
      </button>
      <button class="btn btn-secondary" @click="$emit('edit-params')">
        Edit Parameters
      </button>
      <button class="btn btn-ghost" @click="$emit('regenerate')">
        Regenerate
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ParameterSummary {
  key: string
  label: string
  purpose: string
}

interface StrategySummaryData {
  summary: string
  explanation: string
  parameters: ParameterSummary[]
  confidence?: number
}

defineProps<{
  summary: StrategySummaryData | null
}>()

defineEmits<{
  (event: 'confirm'): void
  (event: 'edit-params'): void
  (event: 'regenerate'): void
}>()
</script>

<style scoped>
.strategy-summary-card {
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.summary-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.confidence-badge {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: var(--color-accent-bg);
  color: var(--color-primary-border);
  border: 1px solid var(--color-primary-border);
}

.summary-text {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.summary-explanation {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--spacing-lg);
}

.param-list {
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.param-list-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
}

.param-item {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.param-key {
  display: block;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.param-purpose {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.summary-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}
</style>
