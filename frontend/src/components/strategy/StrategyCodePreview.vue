<template>
  <div class="code-preview">
    <div class="code-preview__header">
      <span class="code-preview__filename">{{ filename }}</span>
      <button class="btn btn-secondary btn--sm" type="button" @click="handleCopy">
        {{ copied ? $t('strategyPreview.copied') : $t('strategyPreview.copy') }}
      </button>
    </div>
    <pre class="code-preview__body"><code>{{ code }}</code></pre>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  code: string
  filename?: string
}>()

const copied = ref(false)

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(copied.value ? '' : '')
  } catch {
    // fallback handled below
  }
  const el = document.querySelector('.code-preview__body code')
  const text = el?.textContent || ''
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.code-preview {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.code-preview__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-md);
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid var(--color-border);
}

.code-preview__filename {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace);
}

.btn--sm {
  padding: 2px 8px;
  font-size: var(--font-size-xs);
}

.code-preview__body {
  margin: 0;
  padding: var(--spacing-md);
  background: rgba(7, 17, 27, 0.94);
  color: #f8fbff;
  overflow-x: auto;
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace);
  font-size: var(--font-size-sm);
  line-height: 1.65;
  white-space: pre;
  tab-size: 4;
}
</style>
