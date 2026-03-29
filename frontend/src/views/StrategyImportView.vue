<template>
  <section class="strategy-import-view">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Import Strategy</h1>
          <p class="page-subtitle">Upload a Python file, source zip, or existing .qys package.</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies">
          Back to library
        </RouterLink>
      </div>

      <div class="card import-card">
        <label class="field">
          <span class="field-label">Strategy source</span>
          <input class="field-input" type="file" accept=".py,.zip,.qys" @change="handleFileChange" />
        </label>
        <p class="field-help">Supported: single `strategy.py`, source project zip, or `.qys` package.</p>
        <p v-if="selectedFile" class="selected-file">{{ selectedFile.name }}</p>

        <div class="actions">
          <button class="btn btn-primary" type="button" :disabled="loading || !selectedFile" @click="handleAnalyze">
            {{ loading ? 'Analyzing...' : 'Analyze import' }}
          </button>
        </div>

        <p v-if="error" class="message error">{{ error }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { analyzeStrategyImport } from '../api/strategies'

const router = useRouter()
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const error = ref('')

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
  error.value = ''
}

async function handleAnalyze() {
  if (!selectedFile.value) {
    error.value = 'Choose a strategy source first.'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = await analyzeStrategyImport(selectedFile.value)
    sessionStorage.setItem(`strategy-import:${result.draftImportId}`, JSON.stringify(result))
    await router.push({
      name: 'strategy-import-confirm',
      query: { draftImportId: result.draftImportId }
    })
  } catch (err: any) {
    error.value = err?.message || 'Failed to analyze import source'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.strategy-import-view {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.import-card {
  padding: var(--spacing-lg);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.field-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm);
}

.field-help,
.selected-file {
  margin-top: var(--spacing-sm);
  color: var(--color-text-muted);
}

.actions {
  margin-top: var(--spacing-md);
}

.message.error {
  margin-top: var(--spacing-md);
  color: var(--color-danger);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
