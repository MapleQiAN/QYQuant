<template>
  <div class="editor-root">
    <!-- Toolbar -->
    <header class="editor-toolbar">
      <div class="toolbar-left">
        <button class="toolbar-btn" type="button" @click="handleBack">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          {{ t('strategyEditor.toolbarBack') }}
        </button>
        <span class="toolbar-divider"></span>
        <span class="toolbar-title">{{ isEditing ? t('strategyEditor.toolbarEditing') : t('strategyEditor.toolbarNewStrategy') }}</span>
      </div>
      <div class="toolbar-right">
        <button
          class="btn btn-primary btn--compact"
          type="button"
          :disabled="saving || !canSave"
          @click="handleSave"
        >
          <span v-if="saving" class="btn-spinner"></span>
          {{ saving ? t('strategyEditor.toolbarSaving') : t('strategyEditor.toolbarSave') }}
        </button>
      </div>
    </header>

    <div class="editor-body">
      <!-- Sidebar -->
      <aside class="editor-sidebar">
        <h3 class="sidebar-heading">{{ t('strategyEditor.sidebarTitle') }}</h3>

        <label class="form-label">
          {{ t('strategyEditor.sidebarName') }}
          <input v-model="form.name" class="form-input" :placeholder="t('strategyEditor.sidebarNamePlaceholder')" />
        </label>

        <label class="form-label">
          {{ t('strategyEditor.sidebarSymbol') }}
          <input v-model="form.symbol" class="form-input" :placeholder="t('strategyEditor.sidebarSymbolPlaceholder')" />
        </label>

        <label class="form-label">
          {{ t('strategyEditor.sidebarDescription') }}
          <textarea v-model="form.description" class="form-textarea" rows="3" :placeholder="t('strategyEditor.sidebarDescriptionPlaceholder')"></textarea>
        </label>

        <label class="form-label">
          {{ t('strategyEditor.sidebarCategory') }}
          <input v-model="form.category" class="form-input" :placeholder="t('strategyEditor.sidebarCategoryPlaceholder')" />
        </label>

        <label class="form-label">
          {{ t('strategyEditor.sidebarTags') }}
          <input v-model="tagsInput" class="form-input" :placeholder="t('strategyEditor.sidebarTagsPlaceholder')" @blur="syncTags" />
        </label>
      </aside>

      <!-- Monaco Editor -->
      <main ref="editorContainer" class="editor-main"></main>
    </div>

    <!-- Status Bar -->
    <footer class="editor-statusbar">
      <span>{{ t('strategyEditor.statusBarLine') }} {{ cursor.line }}, {{ t('strategyEditor.statusBarCol') }} {{ cursor.col }}</span>
      <span>{{ lineCount }} {{ t('strategyEditor.statusBarLines') }}</span>
      <span :class="syntaxClass">{{ syntaxLabel }}</span>
      <span class="statusbar-right">{{ saveStatusLabel }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { createStrategyWithCode, fetchStrategyCode, updateStrategyCode } from '../api/strategies'
import { toast } from '../lib/toast'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const strategyId = computed(() => (route.params.strategyId as string) || null)
const isEditing = computed(() => Boolean(strategyId.value))

const editorContainer = ref<HTMLElement | null>(null)
const saving = ref(false)
const dirty = ref(false)
const lastSavedAt = ref<number | null>(null)
const autoSaveSource = ref(false)
let editor: any = null
let monacoInstance: any = null
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

const form = reactive({
  name: '',
  symbol: '',
  description: '',
  category: '',
  tags: [] as string[],
})

const tagsInput = ref('')
const cursor = reactive({ line: 1, col: 1 })
const lineCount = ref(1)
const syntaxOk = ref(true)

const canSave = computed(() => form.name.trim() !== '' && form.symbol.trim() !== '')

const syntaxClass = computed(() => syntaxOk.value ? 'status-ok' : 'status-error')
const syntaxLabel = computed(() => syntaxOk.value ? t('strategyEditor.statusBarSyntaxOk') : t('strategyEditor.statusBarSyntaxError'))
const saveStatusLabel = computed(() => {
  if (dirty.value) return t('strategyEditor.statusBarUnsaved')
  if (autoSaveSource.value) return t('strategyEditor.statusBarAutoSaved')
  if (lastSavedAt.value) return t('strategyEditor.statusBarSaved')
  return ''
})

const DRAFT_KEY = 'strategy-editor-draft'

function syncTags() {
  form.tags = tagsInput.value.split(',').map(s => s.trim()).filter(Boolean)
}

function loadFormFromDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const draft = JSON.parse(raw)
    if (draft.form) Object.assign(form, draft.form)
    if (draft.tagsInput) tagsInput.value = draft.tagsInput
    return draft.code as string | undefined
  } catch {
    return undefined
  }
}

function saveDraft(code: string) {
  syncTags()
  localStorage.setItem(DRAFT_KEY, JSON.stringify({ form: { ...form }, tagsInput: tagsInput.value, code }))
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

function scheduleAutoSave() {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(() => {
    const code = editor?.getValue()
    if (code != null) {
      saveDraft(code)
      autoSaveSource.value = true
      dirty.value = false
    }
  }, 3000)
}

async function initEditor() {
  const monaco = await import('monaco-editor')
  monacoInstance = monaco

  let initialCode = t('strategyEditor.editorDefaultCode')

  if (isEditing.value && strategyId.value) {
    try {
      const result = await fetchStrategyCode(strategyId.value)
      initialCode = result.code
      form.name = form.name || ''
      form.symbol = form.symbol || ''
    } catch {
      toast.error(t('strategyEditor.messagesLoadError'))
    }
  } else {
    const draftCode = loadFormFromDraft()
    if (draftCode) {
      initialCode = draftCode
      toast.info(t('strategyEditor.messagesDraftRestored'))
    }
  }

  if (!editorContainer.value) return

  editor = monaco.editor.create(editorContainer.value, {
    value: initialCode,
    language: 'python',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 4,
    padding: { top: 12 },
  })

  lineCount.value = editor.getModel().getLineCount()

  editor.onDidChangeCursorPosition((e: any) => {
    cursor.line = e.position.lineNumber
    cursor.col = e.position.column
  })

  editor.onDidChangeModelContent(() => {
    dirty.value = true
    autoSaveSource.value = false
    lineCount.value = editor.getModel().getLineCount()
    scheduleAutoSave()
  })

  monaco.editor.onDidChangeMarkers((uris: any[]) => {
    const model = editor.getModel()
    if (!model) return
    const uri = model.uri
    if (uris.some(u => u.path === uri.path)) {
      const markers = monaco.editor.getModelMarkers({ resource: uri })
      syntaxOk.value = markers.length === 0
    }
  })
}

async function handleSave() {
  if (!canSave.value || saving.value) return
  saving.value = true
  syncTags()

  const code = editor?.getValue() || ''

  try {
    if (isEditing.value && strategyId.value) {
      await updateStrategyCode(strategyId.value, {
        code,
        metadata: {
          name: form.name,
          description: form.description,
          category: form.category,
          tags: form.tags,
        },
      })
    } else {
      const created = await createStrategyWithCode({
        code,
        name: form.name,
        symbol: form.symbol,
        description: form.description,
        category: form.category,
        tags: form.tags,
      })
      clearDraft()
      await router.replace({ name: 'strategy-editor-edit', params: { strategyId: created.id } })
    }
    dirty.value = false
    lastSavedAt.value = Date.now()
    autoSaveSource.value = false
    toast.success(t('strategyEditor.messagesSaveSuccess'))
  } catch (error: any) {
    toast.error(error?.message || t('strategyEditor.messagesSaveError'))
  } finally {
    saving.value = false
  }
}

async function handleBack() {
  if (dirty.value) {
    const confirmed = window.confirm(t('strategyEditor.messagesUnsavedBody'))
    if (!confirmed) return
  }
  await router.push('/strategies')
}

onMounted(() => {
  void initEditor()
})

onBeforeUnmount(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  editor?.dispose()
})

onBeforeRouteLeave((_to, _from, next) => {
  if (dirty.value) {
    const confirmed = window.confirm(t('strategyEditor.messagesUnsavedBody'))
    next(confirmed)
  } else {
    next()
  }
})
</script>

<style scoped>
.editor-root {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  z-index: 100;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  background: transparent;
  color: #cccccc;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.toolbar-btn:hover {
  background: #2a2d2e;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #3c3c3c;
}

.toolbar-title {
  font-size: 13px;
  font-weight: 600;
  color: #cccccc;
}

.btn--compact {
  padding: 5px 14px;
  font-size: 12px;
}

/* Body */
.editor-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* Sidebar */
.editor-sidebar {
  width: 280px;
  padding: 16px;
  background: #252526;
  border-right: 1px solid #3c3c3c;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-heading {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #888;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #aaa;
}

.form-input,
.form-textarea {
  padding: 6px 8px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  color: #d4d4d4;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #007acc;
}

.form-textarea {
  resize: vertical;
}

/* Editor Main */
.editor-main {
  flex: 1;
  min-width: 0;
}

/* Status Bar */
.editor-statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 24px;
  padding: 0 12px;
  background: #007acc;
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.statusbar-right {
  margin-left: auto;
}

.status-error {
  color: #f48771;
}

/* Responsive */
@media (max-width: 768px) {
  .editor-sidebar {
    display: none;
  }
}
</style>
