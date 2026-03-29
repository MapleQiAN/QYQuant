<template>
  <section class="strategy-import-confirm-view">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Confirm Import</h1>
          <p class="page-subtitle">Review detected entrypoints and fill any missing metadata.</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies/import">
          Back to import
        </RouterLink>
      </div>

      <div v-if="!analysis" class="card panel">
        <p class="message error">Import analysis could not be loaded. Start again from the import page.</p>
      </div>

      <div v-else class="layout-grid">
        <div class="card panel">
          <h2>Import Summary</h2>
          <p>{{ analysis.sourceType }}</p>
          <p>{{ analysis.fileSummary?.filename }}</p>
          <p v-if="analysis.warnings.length" class="message warning">{{ analysis.warnings.join(', ') }}</p>
          <p v-if="analysis.errors.length" class="message error">{{ analysis.errors.join(', ') }}</p>
        </div>

        <div class="card panel">
          <h2>Entrypoint</h2>
          <label class="field">
            <span class="field-label">Selected entrypoint</span>
            <select v-model="selectedEntrypointKey" class="field-input">
              <option
                v-for="candidate in analysis.entrypointCandidates"
                :key="candidate.path + ':' + candidate.callable"
                :value="candidate.path + ':' + candidate.callable"
              >
                {{ candidate.callable }} @ {{ candidate.path }}
              </option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Name</span>
            <input v-model="name" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">Description</span>
            <textarea v-model="description" class="field-input field-textarea" />
          </label>

          <label class="field">
            <span class="field-label">Category</span>
            <input v-model="category" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">Primary symbol</span>
            <input v-model="symbol" class="field-input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">Tags</span>
            <input v-model="tags" class="field-input" type="text" />
          </label>

          <div class="actions">
            <button
              class="btn btn-primary"
              type="button"
              :disabled="submitting || !selectedEntrypoint"
              @click="handleConfirm"
            >
              {{ submitting ? 'Importing...' : 'Confirm import' }}
            </button>
          </div>

          <p v-if="error" class="message error">{{ error }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { confirmStrategyImport } from '../api/strategies'
import type { StrategyImportAnalysis } from '../types/Strategy'

const route = useRoute()
const router = useRouter()
const draftImportId = String(route.query.draftImportId || '')
const rawAnalysis = draftImportId ? sessionStorage.getItem(`strategy-import:${draftImportId}`) : null
const analysis = ref<StrategyImportAnalysis | null>(rawAnalysis ? JSON.parse(rawAnalysis) : null)
const selectedEntrypointKey = ref(
  analysis.value?.entrypointCandidates[0]
    ? `${analysis.value.entrypointCandidates[0].path}:${analysis.value.entrypointCandidates[0].callable}`
    : ''
)
const metadataCandidates = (analysis.value?.metadataCandidates || {}) as Record<string, unknown>
const name = ref(String(metadataCandidates.name || ''))
const description = ref(String(metadataCandidates.description || ''))
const category = ref(String(metadataCandidates.category || 'other'))
const symbol = ref(String(metadataCandidates.symbol || ''))
const tags = ref(Array.isArray(metadataCandidates.tags) ? metadataCandidates.tags.join(', ') : '')
const submitting = ref(false)
const error = ref('')

const selectedEntrypoint = computed(() => {
  return (
    analysis.value?.entrypointCandidates.find(
      (candidate) => `${candidate.path}:${candidate.callable}` === selectedEntrypointKey.value
    ) || null
  )
})

async function handleConfirm() {
  if (!analysis.value || !selectedEntrypoint.value) {
    error.value = 'Select an entrypoint before continuing.'
    return
  }
  if (!name.value.trim()) {
    error.value = 'Strategy name is required.'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    const result = await confirmStrategyImport({
      draftImportId: analysis.value.draftImportId,
      selectedEntrypoint: {
        path: selectedEntrypoint.value.path,
        callable: selectedEntrypoint.value.callable,
        interface: selectedEntrypoint.value.interface || 'event_v1'
      },
      metadata: {
        name: name.value.trim(),
        description: description.value.trim(),
        category: category.value.trim(),
        symbol: symbol.value.trim(),
        tags: tags.value
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)
      },
      parameterDefinitions: analysis.value.parameterCandidates
    })
    sessionStorage.removeItem(`strategy-import:${analysis.value.draftImportId}`)
    if (result.next) {
      await router.push(result.next)
    }
  } catch (err: any) {
    error.value = err?.message || 'Failed to confirm strategy import'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.strategy-import-confirm-view {
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

.layout-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
  gap: var(--spacing-lg);
}

.panel {
  padding: var(--spacing-lg);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
}

.field-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm);
}

.field-textarea {
  min-height: 96px;
}

.actions {
  margin-top: var(--spacing-lg);
}

.message.warning {
  color: var(--color-warning);
}

.message.error {
  color: var(--color-danger);
}

@media (max-width: 768px) {
  .page-header,
  .layout-grid {
    display: flex;
    flex-direction: column;
  }
}
</style>
