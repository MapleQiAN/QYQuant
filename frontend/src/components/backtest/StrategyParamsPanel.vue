<template>
  <section class="params-panel">
    <div class="params-panel__header">
      <h3 class="params-panel__title">{{ $t('backtestReport.strategyParamsTitle') }}</h3>
      <p class="params-panel__subtitle">{{ $t('backtestReport.strategyParamsSubtitle') }}</p>
    </div>

    <div class="params-grid">
      <article v-if="strategyId" class="param-tile">
        <span class="param-tile__label">{{ $t('backtestReport.strategyId') }}</span>
        <strong class="param-tile__value mono">{{ strategyId }}</strong>
      </article>

      <article v-if="version" class="param-tile">
        <span class="param-tile__label">{{ $t('backtestReport.strategyVersion') }}</span>
        <strong class="param-tile__value mono">{{ version }}</strong>
      </article>

      <article v-if="(symbols ?? []).length" class="param-tile">
        <span class="param-tile__label">{{ $t('backtestReport.symbols') }}</span>
        <strong class="param-tile__value mono">{{ (symbols ?? []).join(', ') }}</strong>
      </article>

      <article v-if="interval" class="param-tile">
        <span class="param-tile__label">{{ $t('backtestReport.interval') }}</span>
        <strong class="param-tile__value mono">{{ interval }}</strong>
      </article>

      <article v-if="dataSource" class="param-tile">
        <span class="param-tile__label">{{ $t('backtestReport.dataSource') }}</span>
        <strong class="param-tile__value mono">{{ dataSource }}</strong>
      </article>
    </div>

    <div v-if="paramEntries.length" class="params-detail">
      <h4 class="params-detail__title">{{ $t('backtestReport.strategyParams') }}</h4>
      <div class="params-detail__grid">
        <div v-for="[key, value] in paramEntries" :key="key" class="params-detail__row">
          <span class="params-detail__key mono">{{ key }}</span>
          <span class="params-detail__value mono">{{ JSON.stringify(value) }}</span>
        </div>
      </div>
    </div>

    <div v-if="!strategyId && !paramEntries.length" class="params-panel__empty">
      {{ $t('backtestReport.noParams') }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  strategyId?: string
  version?: string
  symbols?: string[]
  interval?: string
  dataSource?: string
  params?: Record<string, unknown>
}>()

const paramEntries = computed(() => {
  const entries = Object.entries(props.params ?? {})
  return entries.filter(([, v]) => v !== undefined && v !== null && v !== '')
})
</script>

<style scoped>
.params-panel {
  display: grid;
  gap: 16px;
  padding: 22px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.params-panel::before {
  content: "";
  position: absolute;
  width: 44px;
  height: 44px;
  background: var(--color-primary);
  top: -12px;
  right: -12px;
  border-radius: 50%;
  opacity: 0.9;
}

.params-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.params-panel__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
}

.params-panel__subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.params-panel__empty {
  padding: 16px;
  border-radius: var(--radius-sm);
  text-align: center;
  color: var(--color-text-muted);
  background: #fafafa;
  border: 2px dashed var(--color-border-light);
  position: relative;
  z-index: 1;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
  position: relative;
  z-index: 1;
}

.param-tile {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: #fafafa;
  border: 2px solid var(--color-border-light);
}

.param-tile__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.param-tile__value {
  font-size: var(--font-size-md);
  font-weight: 800;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.params-detail__title {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 700;
  position: relative;
  z-index: 1;
}

.params-detail__grid {
  display: grid;
  gap: 6px;
  margin-top: 8px;
  position: relative;
  z-index: 1;
}

.params-detail__row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: #fafafa;
  border: 2px dashed var(--color-border-light);
}

.params-detail__key {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  min-width: 120px;
}

.params-detail__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.mono {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .params-grid {
    grid-template-columns: 1fr;
  }

  .params-detail__row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
