<template>
  <div class="export-panel">
    <button
      class="btn btn-primary"
      type="button"
      :disabled="exporting"
      @click="$emit('export', 'qys')"
    >
      <span v-if="exporting && activeFormat === 'qys'" class="btn-spinner"></span>
      {{ $t('strategyPreview.exportQys') }}
    </button>
    <button
      class="btn btn-secondary"
      type="button"
      :disabled="exporting"
      @click="$emit('export', 'py')"
    >
      <span v-if="exporting && activeFormat === 'py'" class="btn-spinner"></span>
      {{ $t('strategyPreview.exportPy') }}
    </button>
    <button
      class="btn btn-primary"
      type="button"
      :disabled="saving"
      @click="$emit('save')"
    >
      <span v-if="saving" class="btn-spinner"></span>
      {{ $t('strategyPreview.saveStrategy') }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  exporting: boolean
  activeFormat: string
  saving: boolean
}>()

defineEmits<{
  export: [format: 'qys' | 'py']
  save: []
}>()
</script>

<style scoped>
.export-panel {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
}

.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
