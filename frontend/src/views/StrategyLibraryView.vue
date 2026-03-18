<template>
  <section class="strategy-library">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Strategy Library</h1>
          <p class="page-subtitle">Manage imported strategies and bring new .qys packages into your workspace.</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/">
          Back to dashboard
        </RouterLink>
      </div>

      <section v-if="isGuidedMode" :class="['card guided-card', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'guided-strategy-card' }]" data-onboarding-target="guided-strategy-card">
        <div class="section-header">
          <h2>Guided Strategy</h2>
          <p>Pick the recommended onboarding strategy to complete your first backtest with fewer decisions.</p>
        </div>
        <div v-if="guidedLoading" class="empty-state">Loading guided strategies...</div>
        <p v-else-if="guidedError" class="message error">{{ guidedError }}</p>
        <div v-else-if="guidedStrategies.length" class="strategy-list">
          <article v-for="strategy in guidedStrategies" :key="strategy.id" class="strategy-row guided-row">
            <div class="row-main">
              <div class="row-title">{{ strategy.name }}</div>
              <div class="row-meta">
                <span>{{ strategy.symbol }}</span>
                <span>{{ strategy.category || 'beginner' }}</span>
              </div>
              <div class="tag-row">
                <span v-for="tag in strategy.tags" :key="tag" class="pill">{{ tag }}</span>
              </div>
            </div>
            <div class="guided-actions">
              <button class="btn btn-secondary" type="button" @click="handleGuidedPreview(strategy.id)">
                View details
              </button>
              <button class="btn btn-primary" type="button" @click="handleGuidedSelect(strategy.id)">
                Use this strategy
              </button>
            </div>
          </article>
        </div>
      </section>

      <div class="layout-grid">
        <div class="card import-card">
          <div class="section-header">
            <h2>Import Strategy</h2>
            <p>Drop a `.qys` package here or pick a file from disk.</p>
          </div>

          <label
            class="dropzone"
            :class="{ active: dragActive }"
            data-test="dropzone"
            @dragenter.prevent="dragActive = true"
            @dragover.prevent="dragActive = true"
            @dragleave.prevent="dragActive = false"
            @drop.prevent="handleDrop"
          >
            <input class="file-input" type="file" accept=".qys,.zip" @change="handleFileChange" />
            <span class="dropzone-title">{{ selectedFile ? selectedFile.name : 'Drop .qys file here' }}</span>
            <span class="dropzone-help">{{ selectedFile ? formatBytes(selectedFile.size) : 'Supported size: up to 10 MB' }}</span>
          </label>

          <div class="actions">
            <button
              class="btn btn-primary"
              type="button"
              data-test="import-submit"
              :disabled="importing || !selectedFile"
              @click="handleImport"
            >
              {{ importing ? 'Importing...' : 'Import package' }}
            </button>
          </div>

          <p v-if="importError" class="message error">{{ importError }}</p>

          <div v-if="preview" class="preview-card">
            <div class="preview-title">{{ preview.name }}</div>
            <div class="preview-text">{{ preview.description || 'No description provided.' }}</div>
            <div class="tag-row">
              <span class="pill">{{ preview.category || 'other' }}</span>
              <span v-for="tag in preview.tags" :key="tag" class="pill">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div class="card library-card">
          <div class="section-header">
            <h2>My Strategies</h2>
            <p>{{ total }} item<span v-if="total !== 1">s</span> in your private library.</p>
          </div>

          <div v-if="loading" class="empty-state">Loading strategy library...</div>
          <p v-else-if="loadError" class="message error">{{ loadError }}</p>
          <div v-else-if="items.length === 0" class="empty-state">No strategies yet. Import your first package.</div>
          <div v-else class="strategy-list">
            <article v-for="strategy in items" :key="strategy.id" class="strategy-row">
              <div class="row-main">
                <div class="row-title">{{ strategy.name }}</div>
                <div class="row-meta">
                  <span>{{ strategy.category || 'other' }}</span>
                  <span>{{ strategy.source || 'upload' }}</span>
                  <span>{{ formatCreatedAt(strategy.createdAt) }}</span>
                </div>
                <p class="row-description">{{ strategy.description || 'No description provided.' }}</p>
                <div class="tag-row">
                  <span v-for="tag in strategy.tags" :key="tag" class="pill">{{ tag }}</span>
                </div>
              </div>
              <button
                class="btn btn-secondary danger"
                type="button"
                :data-test="`delete-${strategy.id}`"
                @click="handleDelete(strategy.id)"
              >
                Delete
              </button>
            </article>
          </div>

          <div class="pagination">
            <button class="btn btn-secondary" type="button" :disabled="page <= 1 || loading" @click="changePage(page - 1)">
              Previous
            </button>
            <span>Page {{ page }} / {{ totalPages }}</span>
            <button
              class="btn btn-secondary"
              type="button"
              :disabled="page >= totalPages || loading"
              @click="changePage(page + 1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { deleteStrategy, fetchMarketplaceStrategies, fetchStrategies, importStrategy } from '../api/strategies'
import type { Strategy } from '../types/Strategy'
import { useUserStore } from '../stores'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const items = ref<Strategy[]>([])
const guidedStrategies = ref<Strategy[]>([])
const loading = ref(false)
const loadError = ref('')
const guidedLoading = ref(false)
const guidedError = ref('')
const importError = ref('')
const importing = ref(false)
const dragActive = ref(false)
const selectedFile = ref<File | null>(null)
const preview = ref<Strategy | null>(null)
const page = ref(1)
const perPage = ref(10)
const total = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage.value)))
const isGuidedMode = computed(() => route.query.guided === 'true')

onMounted(() => {
  void loadPage(1)
  if (isGuidedMode.value) {
    void loadGuidedStrategies()
  }
})

async function loadPage(nextPage: number) {
  loading.value = true
  loadError.value = ''
  try {
    const result = await fetchStrategies({ page: nextPage, perPage: perPage.value })
    items.value = result.items
    page.value = result.page
    perPage.value = result.perPage
    total.value = result.total
  } catch (error: any) {
    loadError.value = error?.message || 'Failed to load strategy library'
  } finally {
    loading.value = false
  }
}

function changePage(nextPage: number) {
  void loadPage(nextPage)
}

async function loadGuidedStrategies() {
  guidedLoading.value = true
  guidedError.value = ''
  try {
    guidedStrategies.value = await fetchMarketplaceStrategies({ tag: 'onboarding' })
  } catch (error: any) {
    guidedError.value = error?.message || 'Failed to load guided strategies'
  } finally {
    guidedLoading.value = false
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
  preview.value = null
  importError.value = ''
}

function handleDrop(event: DragEvent) {
  dragActive.value = false
  selectedFile.value = event.dataTransfer?.files?.[0] || null
  preview.value = null
  importError.value = ''
}

async function handleImport() {
  if (!selectedFile.value) {
    importError.value = 'Please choose a .qys package first.'
    return
  }

  importError.value = ''
  importing.value = true
  try {
    const result = await importStrategy(selectedFile.value)
    preview.value = result.strategy
    selectedFile.value = null
    await loadPage(1)
    if (result.next) {
      await router.push(result.next)
    }
  } catch (error: any) {
    importError.value = error?.message || 'Failed to import strategy package'
  } finally {
    importing.value = false
  }
}

async function handleDelete(strategyId: string) {
  if (!window.confirm('Delete this strategy?')) {
    return
  }

  await deleteStrategy(strategyId)
  const fallbackPage = items.value.length === 1 && page.value > 1 ? page.value - 1 : page.value
  await loadPage(fallbackPage)
}

async function handleGuidedSelect(strategyId: string) {
  userStore.setGuidedBacktestStrategy(strategyId)
  userStore.setGuidedBacktestStep(2)
  userStore.setOnboardingHighlightTarget('guided-run-button')
  await router.push({
    name: 'strategy-parameters',
    params: { strategyId },
    query: { guided: 'true' },
  })
}

async function handleGuidedPreview(strategyId: string) {
  await router.push({
    name: 'strategy-detail',
    params: { strategyId },
  })
}

function formatBytes(bytes: number) {
  if (bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / Math.pow(1024, index)).toFixed(1)} ${units[index]}`
}

function formatCreatedAt(value?: string | number) {
  if (!value) return 'Unknown time'
  const numeric = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(numeric)) return String(value)
  return new Date(numeric).toLocaleDateString()
}
</script>

<style scoped>
.strategy-library {
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
  color: var(--color-text-primary);
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.1fr);
  gap: var(--spacing-lg);
}

.guided-card {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
}

.guided-row {
  align-items: center;
}

.guided-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.import-card,
.library-card {
  padding: var(--spacing-lg);
}

.section-header h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.section-header p {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-lg);
  min-height: 180px;
  padding: var(--spacing-lg);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, rgba(18, 58, 84, 0.03), rgba(18, 58, 84, 0.08));
  cursor: pointer;
  transition: border-color var(--transition-fast), transform var(--transition-fast);
}

.dropzone.active {
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

.file-input {
  display: none;
}

.dropzone-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.dropzone-help {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.actions {
  margin-top: var(--spacing-md);
}

.preview-card {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  border: 1px solid var(--color-primary-light);
}

.preview-title,
.row-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.preview-text,
.row-description {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-secondary);
}

.strategy-list {
  margin-top: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.strategy-row {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface);
}

.row-main {
  flex: 1;
  min-width: 0;
}

.row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--color-background);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.message.error {
  margin-top: var(--spacing-md);
  color: var(--color-danger);
}

.empty-state {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
}

.danger {
  white-space: nowrap;
}

@media (max-width: 960px) {
  .page-header,
  .layout-grid,
  .strategy-row,
  .pagination,
  .guided-actions {
    display: flex;
    flex-direction: column;
  }
}
</style>
