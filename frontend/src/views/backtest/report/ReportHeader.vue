<template>
  <div class="page-header" data-test="report-header">
    <div class="header-left">
      <div class="header-badges">
        <span class="eyebrow">{{ $t('backtestReport.eyebrow') }}</span>
        <span class="job-chip">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          JOB&nbsp;<span class="job-chip__id">{{ jobId }}</span>
        </span>
      </div>
      <h1 class="page-title">{{ $t('backtestReport.title') }}</h1>
      <p class="page-subtitle">{{ $t('backtestReport.subtitle', { jobId }) }}</p>
    </div>
    <div v-if="canExport" class="header-actions" data-export-ignore="true">
      <button class="btn btn-secondary" type="button" data-test="export-html" @click="$emit('export-html')">
        {{ $t('backtestReport.exportHtml') }}
      </button>
      <button class="btn btn-primary" type="button" data-test="export-pdf" @click="$emit('export-pdf')">
        {{ $t('backtestReport.exportPdf') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  jobId: string
  canExport: boolean
}>()

defineEmits<{
  'export-html': []
  'export-pdf': []
}>()
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-xl);
}

.header-left {
  flex: 1;
  min-width: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.header-badges {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.eyebrow {
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.job-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
}

.job-chip__id {
  font-family: 'DM Mono', monospace;
  color: var(--color-primary);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 900;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
