<template>
  <div class="panel">
    <div v-if="title || $slots.actions" class="panel-header">
      <div class="panel-title-group">
        <span v-if="title" class="panel-title">{{ title }}</span>
        <span v-if="subtitle" class="panel-subtitle">{{ subtitle }}</span>
        <slot name="badge" />
      </div>
      <div v-if="$slots.actions" class="panel-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="panel-body" :class="{ 'no-padding': noPadding }">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  noPadding?: boolean
}

withDefaults(defineProps<Props>(), {
  noPadding: false,
})
</script>

<style scoped>
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--panel-header-height);
  padding: 0 var(--spacing-md);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.panel-title-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.panel-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.panel-subtitle {
  font-size: var(--font-size-2xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.panel-body {
  flex: 1;
  padding: var(--spacing-md);
  overflow: auto;
}

.panel-body.no-padding {
  padding: 0;
}
</style>
