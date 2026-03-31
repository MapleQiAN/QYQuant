<template>
  <section class="strategy-import-view">
    <div class="container">
      <div class="page-header">
        <div>
          <p class="eyebrow">{{ t('strategy.import.pageTitle') }}</p>
          <h1 class="page-title">{{ t('strategy.import.pageTitle') }}</h1>
          <p class="page-subtitle">{{ t('strategy.import.pageSubtitle') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          {{ t('strategy.import.backToLibrary') }}
        </RouterLink>
      </div>

      <div class="card import-card">
        <div
          class="drop-zone"
          :class="{ 'drop-zone--active': isDragging, 'drop-zone--has-file': selectedFile }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInputRef"
            class="drop-zone__input"
            type="file"
            accept=".py,.zip,.qys"
            @change="handleFileChange"
          />

          <div v-if="selectedFile" class="drop-zone__file">
            <div class="file-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div class="file-info">
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
            </div>
            <button class="file-clear" type="button" @click.stop="clearFile">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div v-else class="drop-zone__prompt">
            <div class="drop-zone__icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <p class="drop-zone__title">{{ t('strategy.import.strategySource') }}</p>
            <p class="drop-zone__hint">{{ t('strategy.import.supportedFormats') }}</p>
            <div class="drop-zone__formats">
              <span class="format-chip">.py</span>
              <span class="format-chip">.zip</span>
              <span class="format-chip format-chip--accent">.qys</span>
            </div>
          </div>
        </div>

        <div class="import-actions">
          <button class="btn btn-primary" type="button" :disabled="loading || !selectedFile" @click="handleAnalyze">
            <span v-if="loading" class="btn-spinner"></span>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            {{ loading ? t('strategy.import.analyzing') : t('strategy.import.analyzeButton') }}
          </button>
        </div>

        <p v-if="error" class="message error">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {{ error }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import { analyzeStrategyImport } from '../api/strategies'
import { toast } from '../lib/toast'

const { t } = useI18n()

const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const error = ref('')
const isDragging = ref(false)

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
  error.value = ''
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    selectedFile.value = file
    error.value = ''
  }
}

function clearFile() {
  selectedFile.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function handleAnalyze() {
  if (!selectedFile.value) {
    error.value = t('strategy.import.chooseSourceFirst')
    toast.error(error.value)
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = await analyzeStrategyImport(selectedFile.value)
    sessionStorage.setItem(`strategy-import:${result.draftImportId}`, JSON.stringify(result))
    toast.success('导入分析已生成')
    await router.push({
      name: 'strategy-import-confirm',
      query: { draftImportId: result.draftImportId }
    })
  } catch (err: any) {
    error.value = err?.message || t('strategy.import.failedToAnalyze')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}

.strategy-import-view {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.eyebrow {
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.import-card {
  padding: var(--spacing-lg);
  max-width: 640px;
}

.import-card:hover {
  transform: none;
}

/* ── Drop Zone ── */
.drop-zone {
  position: relative;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xxl) var(--spacing-lg);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.drop-zone:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.drop-zone--active {
  border-color: var(--color-accent);
  background: rgba(0, 217, 255, 0.06);
  border-style: solid;
}

.drop-zone--has-file {
  border-style: solid;
  border-color: var(--color-primary-border);
  background: var(--color-surface-elevated);
  padding: var(--spacing-lg);
}

.drop-zone__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  pointer-events: none;
}

.drop-zone__prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.drop-zone__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  margin-bottom: var(--spacing-sm);
}

.drop-zone__title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
}

.drop-zone__hint {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  max-width: 320px;
  line-height: 1.5;
}

.drop-zone__formats {
  display: flex;
  gap: 4px;
  margin-top: var(--spacing-xs);
}

.format-chip {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 700;
}

.format-chip--accent {
  border-color: var(--color-primary-border);
  color: var(--color-accent);
  background: var(--color-primary-bg);
}

/* ── Selected File ── */
.drop-zone__file {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  flex-shrink: 0;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  text-align: left;
}

.file-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.file-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}

.file-clear:hover {
  background: rgba(255, 59, 59, 0.08);
  border-color: rgba(255, 59, 59, 0.2);
  color: var(--color-danger);
}

/* ── Actions ── */
.import-actions {
  margin-top: var(--spacing-lg);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.message.error {
  margin-top: var(--spacing-md);
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .import-card {
    max-width: none;
  }
}
</style>
