<template>
  <section class="strategy-preview-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">{{ $t('strategyPreview.eyebrow') }}</p>
          <h1 class="page-title">{{ strategyName }}</h1>
          <p v-if="strategyDescription" class="page-subtitle">{{ strategyDescription }}</p>
        </div>
        <RouterLink class="btn btn-secondary" :to="backRoute">
          <ArrowLeftIcon />
          {{ $t('strategyPreview.back') }}
        </RouterLink>
      </div>

      <div v-if="!analysis" class="card panel">
        <p class="message error">{{ $t('strategyPreview.noData') }}</p>
      </div>

      <template v-else>
        <div class="actions-bar">
          <StrategyExportPanel
            :exporting="exporting"
            :active-format="activeExportFormat"
            :saving="saving"
            @export="handleExport"
            @save="handleSave"
          />
        </div>

        <div class="main-grid">
          <aside class="sidebar">
            <div class="card panel">
              <StrategyReportCard :metadata="metadata" />
            </div>

            <div class="card panel">
              <h3 class="panel-title">{{ $t('strategyPreview.parametersTitle') }}</h3>
              <div class="param-groups">
                <div v-for="group in parameterGroups" :key="group.name" class="param-group">
                  <h4 class="param-group__name">{{ group.name }}</h4>
                  <div class="param-group__items">
                    <div v-for="param in group.params" :key="param.key" class="param-field">
                      <label class="param-field__label">
                        <span class="param-field__name">{{ getUserFacingLabel(param) }}</span>
                        <span v-if="param.user_facing?.hint" class="param-field__hint">{{ param.user_facing.hint }}</span>
                      </label>
                      <div class="param-field__input-row">
                        <input
                          v-if="param.type === 'integer' || param.type === 'number'"
                          type="number"
                          class="field-input"
                          :value="editedParams[param.key] ?? param.default"
                          :min="param.min"
                          :max="param.max"
                          :step="param.step || (param.type === 'integer' ? 1 : 0.1)"
                          @input="updateParam(param.key, $event)"
                        />
                        <select
                          v-else-if="param.type === 'enum' && param.enum"
                          class="field-input"
                          :value="editedParams[param.key] ?? param.default"
                          @change="updateParam(param.key, $event)"
                        >
                          <option v-for="opt in param.enum" :key="String(opt)" :value="opt">{{ opt }}</option>
                        </select>
                        <input
                          v-else
                          type="text"
                          class="field-input"
                          :value="editedParams[param.key] ?? param.default"
                          @input="updateParam(param.key, $event)"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          <main class="content">
            <div class="card panel">
              <div class="tab-bar">
                <button
                  class="tab-btn"
                  :class="{ 'tab-btn--active': activeTab === 'report' }"
                  type="button"
                  @click="activeTab = 'report'"
                >
                  {{ $t('strategyPreview.tabReport') }}
                </button>
                <button
                  class="tab-btn"
                  :class="{ 'tab-btn--active': activeTab === 'code' }"
                  type="button"
                  @click="activeTab = 'code'"
                >
                  {{ $t('strategyPreview.tabCode') }}
                </button>
                <button
                  class="tab-btn"
                  :class="{ 'tab-btn--active': activeTab === 'params' }"
                  type="button"
                  @click="activeTab = 'params'"
                >
                  {{ $t('strategyPreview.tabParams') }}
                </button>
              </div>

              <div v-if="activeTab === 'report'" class="tab-content">
                <StrategyReportCard :metadata="metadata" />
              </div>

              <div v-if="activeTab === 'code'" class="tab-content">
                <div v-if="codeLoading" class="code-loading">{{ $t('strategyPreview.loadingCode') }}</div>
                <div v-else-if="codeError" class="code-error">{{ codeError }}</div>
                <div v-else ref="editorContainer" class="code-editor"></div>
              </div>

              <div v-if="activeTab === 'params'" class="tab-content">
                <table class="params-table">
                  <thead>
                    <tr>
                      <th>{{ $t('strategyPreview.paramKey') }}</th>
                      <th>{{ $t('strategyPreview.paramLabel') }}</th>
                      <th>{{ $t('strategyPreview.paramType') }}</th>
                      <th>{{ $t('strategyPreview.paramDefault') }}</th>
                      <th>{{ $t('strategyPreview.paramRange') }}</th>
                      <th>{{ $t('strategyPreview.paramDesc') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="param in parameters" :key="param.key">
                      <td class="mono">{{ param.key }}</td>
                      <td>{{ getUserFacingLabel(param) }}</td>
                      <td>{{ param.type }}</td>
                      <td>{{ param.default }}</td>
                      <td>{{ formatRange(param) }}</td>
                      <td>{{ param.description || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </main>
        </div>

        <AiSuggestionBar
          :suggestions="aiSuggestions"
          @apply="handleApplySuggestion"
        />
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { confirmStrategyImport, exportStrategy, fetchDraftCode } from '../api/strategies'
import { toast } from '../lib/toast'
import type { AiStrategyMetadata, StrategyImportAnalysis, StrategyImportConfirmPayload, StrategyParameter } from '../types/Strategy'
import StrategyReportCard from '../components/strategy/StrategyReportCard.vue'
import StrategyExportPanel from '../components/strategy/StrategyExportPanel.vue'
import AiSuggestionBar from '../components/strategy/AiSuggestionBar.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const draftImportId = String(route.query.draftImportId || '')
const source = String(route.query.source || 'ai')

const rawAnalysis = draftImportId ? sessionStorage.getItem(`strategy-import:${draftImportId}`) : null
const analysis = ref<StrategyImportAnalysis | null>(rawAnalysis ? JSON.parse(rawAnalysis) : null)

const activeTab = ref<'report' | 'code' | 'params'>('report')
const exporting = ref(false)
const activeExportFormat = ref<'qys' | 'py'>('qys')
const saving = ref(false)

const metadata = computed<AiStrategyMetadata>(() => {
  const raw = (analysis.value?.metadataCandidates || {}) as Record<string, unknown>
  return {
    name: String(raw.name || ''),
    description: String(raw.description || ''),
    category: String(raw.category || ''),
    symbol: String(raw.symbol || ''),
    timeframe: raw.timeframe ? String(raw.timeframe) : undefined,
    riskLevel: (raw.riskLevel as AiStrategyMetadata['riskLevel']) || undefined,
    logicExplanation: raw.logicExplanation ? String(raw.logicExplanation) : undefined,
    riskRules: raw.riskRules ? String(raw.riskRules) : undefined,
    suitableMarket: raw.suitableMarket ? String(raw.suitableMarket) : undefined,
    version: raw.version ? String(raw.version) : undefined,
    tags: Array.isArray(raw.tags) ? raw.tags as string[] : undefined,
  }
})

const parameters = computed<StrategyParameter[]>(() =>
  (analysis.value?.parameterCandidates || []) as StrategyParameter[]
)

const editedParams = ref<Record<string, unknown>>({})

const strategyName = computed(() => metadata.value.name || t('strategyPreview.untitled'))
const strategyDescription = computed(() => metadata.value.description || '')

const rawCode = ref('')
const codeLoading = ref(false)
const codeError = ref('')
const editedCode = ref('')
const codeDirty = ref(false)
const editorContainer = ref<HTMLElement | null>(null)
let editor: any = null

async function initEditor() {
  if (!editorContainer.value || !rawCode.value) return
  const monaco = await import('monaco-editor')
  editor = monaco.editor.create(editorContainer.value, {
    value: editedCode.value,
    language: 'python',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 13,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    padding: { top: 12 },
  })
  editor.onDidChangeModelContent(() => {
    editedCode.value = editor.getValue()
    codeDirty.value = editedCode.value !== rawCode.value
  })
}

onMounted(async () => {
  if (!draftImportId) return
  codeLoading.value = true
  try {
    const result = await fetchDraftCode(draftImportId)
    rawCode.value = result.code
    editedCode.value = result.code
  } catch (err: any) {
    codeError.value = err?.message || 'Failed to load strategy code'
  } finally {
    codeLoading.value = false
    await initEditor()
  }
})

onBeforeUnmount(() => {
  editor?.dispose()
})

const backRoute = computed(() => {
  if (source === 'ai') return '/strategies/ai-lab'
  if (source === 'template') return '/strategies/new'
  return '/strategies/import'
})

const parameterGroups = computed(() => {
  const groups = new Map<string, StrategyParameter[]>()
  for (const param of parameters.value) {
    const group = param.user_facing && 'group' in param.user_facing
      ? String(param.user_facing.group)
      : t('strategyPreview.defaultGroup')
    if (!groups.has(group)) groups.set(group, [])
    groups.get(group)!.push(param)
  }
  return Array.from(groups.entries()).map(([name, params]) => ({ name, params }))
})

const aiSuggestions = computed<string[]>(() => {
  const suggestions: string[] = []
  const level = metadata.value.riskLevel
  if (level === 'high') suggestions.push(t('strategyPreview.suggestTightenStop'))
  if (level === 'low') suggestions.push(t('strategyPreview.suggestRelaxStop'))
  if (parameters.value.length > 0) suggestions.push(t('strategyPreview.suggestOptimize'))
  suggestions.push(t('strategyPreview.suggestBacktest'))
  return suggestions
})

function getUserFacingLabel(param: StrategyParameter): string {
  if (param.user_facing && 'label' in param.user_facing) {
    return String(param.user_facing.label)
  }
  return param.key
}

function formatRange(param: StrategyParameter): string {
  if (param.min == null && param.max == null) return '-'
  return `${param.min ?? ''} ~ ${param.max ?? ''}`
}

function updateParam(key: string, event: Event) {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  const raw = target.value
  editedParams.value = { ...editedParams.value, [key]: raw }
}

async function handleExport(format: 'qys' | 'py') {
  if (!analysis.value) return
  exporting.value = true
  activeExportFormat.value = format
  try {
    const blob = await exportStrategy({
      draftImportId: analysis.value.draftImportId,
      format,
      metadata: { ...metadata.value } as Record<string, unknown>,
      parameterDefinitions: parameters.value.map((p) => {
        const edited = { ...p }
        if (edited.key in editedParams.value) {
          edited.default = editedParams.value[edited.key]
        }
        return edited as Record<string, unknown>
      }),
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${metadata.value.name || 'strategy'}.${format === 'qys' ? 'qys' : 'py'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success(t('strategyPreview.exportSuccess'))
  } catch (err: any) {
    toast.error(err?.message || t('strategyPreview.exportFailed'))
  } finally {
    exporting.value = false
  }
}

async function handleSave() {
  if (!analysis.value) return
  saving.value = true
  try {
    const entrypoint = analysis.value.entrypointCandidates[0]
    if (!entrypoint) {
      toast.error(t('strategyPreview.noEntrypoint'))
      return
    }
    const mergedAnalysis = { ...analysis.value }
    if (Object.keys(editedParams.value).length > 0) {
      mergedAnalysis.parameterCandidates = parameters.value.map((p) => ({
        ...p,
        default: p.key in editedParams.value ? editedParams.value[p.key] : p.default,
      }))
    }
    sessionStorage.setItem(`strategy-import:${analysis.value.draftImportId}`, JSON.stringify(mergedAnalysis))

    const confirmPayload: StrategyImportConfirmPayload = {
      draftImportId: analysis.value.draftImportId,
      selectedEntrypoint: {
        path: entrypoint.path,
        callable: entrypoint.callable,
        interface: entrypoint.interface || 'event_v1',
      },
      metadata: {
        name: metadata.value.name,
        description: metadata.value.description,
        category: metadata.value.category,
        symbol: metadata.value.symbol,
        tags: metadata.value.tags || [],
        version: metadata.value.version,
      },
      parameterDefinitions: mergedAnalysis.parameterCandidates as StrategyParameter[],
    }
    if (codeDirty.value) {
      confirmPayload.codeOverride = editedCode.value
    }
    const result = await confirmStrategyImport(confirmPayload)
    sessionStorage.removeItem(`strategy-import:${analysis.value.draftImportId}`)
    toast.success(t('strategyPreview.saveSuccess', { name: result.strategy.name }))
    if (result.next) {
      await router.push({ path: result.next, query: { guided: 'true', source } })
    }
  } catch (err: any) {
    toast.error(err?.message || t('strategyPreview.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleApplySuggestion(suggestion: string) {
  if (suggestion === t('strategyPreview.suggestTightenStop') || suggestion === t('strategyPreview.suggestRelaxStop')) {
    await router.push({ path: '/strategies/ai-lab', query: { refine: suggestion } })
  } else if (suggestion === t('strategyPreview.suggestOptimize') || suggestion === t('strategyPreview.suggestBacktest')) {
    await handleSave()
  } else {
    toast.info(t('strategyPreview.suggestionApplied', { suggestion }))
  }
}

const ArrowLeftIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
}, [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'm12 19-7-7 7-7' }),
])
</script>

<style scoped>
.strategy-preview-view {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
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
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
}

.actions-bar {
  margin-bottom: var(--spacing-lg);
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
  gap: var(--spacing-lg);
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.panel {
  padding: var(--spacing-lg);
}

.panel-title {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-size-md);
}

.param-groups {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.param-group__name {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.param-group__items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-field__label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-field__name {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.param-field__hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.param-field__input-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.field-input {
  width: 100%;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.tab-bar {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--spacing-lg);
}

.tab-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.2s;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn--active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-content {
  min-height: 200px;
}

.params-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.params-table th {
  text-align: left;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.params-table td {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.mono {
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace);
}

.message {
  margin: var(--spacing-md) 0 0;
}

.error {
  color: var(--color-danger);
}

.code-loading {
  padding: var(--spacing-xl);
  text-align: center;
  color: var(--color-text-muted);
}

.code-error {
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-danger);
}

.code-editor {
  min-height: 400px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

@media (max-width: 900px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
