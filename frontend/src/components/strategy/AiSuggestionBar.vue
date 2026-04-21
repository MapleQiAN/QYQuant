<template>
  <div v-if="suggestions.length" class="suggestion-bar">
    <span class="suggestion-bar__label">{{ $t('strategyPreview.aiSuggestions') }}</span>
    <div class="suggestion-bar__actions">
      <button
        v-for="(suggestion, index) in suggestions"
        :key="index"
        class="btn btn-secondary btn--sm"
        type="button"
        @click="$emit('apply', suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  suggestions: string[]
}>()

defineEmits<{
  apply: [suggestion: string]
}>()
</script>

<style scoped>
.suggestion-bar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  background: rgba(64, 162, 255, 0.04);
}

.suggestion-bar__label {
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.suggestion-bar__actions {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.btn--sm {
  padding: 4px 10px;
  font-size: var(--font-size-xs);
}
</style>
