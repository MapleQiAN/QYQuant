<template>
  <section class="strategy-preview-view">
    <div class="container">
      <!-- Header -->
      <div class="page-header">
        <RouterLink class="btn btn-ghost btn--back" :to="backRoute">
          <ArrowLeftIcon />
          {{ $t('strategyPreview.back') }}
        </RouterLink>
        <div class="header-info">
          <p class="eyebrow">{{ $t('strategyPreview.eyebrow') }}</p>
          <h1 class="page-title">{{ strategyName }}</h1>
          <p v-if="strategyDescription" class="page-subtitle">{{ strategyDescription }}</p>
        </div>
        <StrategyExportPanel
          v-if="analysis"
          :exporting="exporting"
          :active-format="activeExportFormat"
          :saving="saving"
          @export="handleExport"
          @save="handleSave"
        />
      </div>

      <div v-if="!analysis" class="card panel">
        <p class="message error">{{ $t('strategyPreview.noData') }}</p>
      </div>

      <template v-else>
        <!-- Sticky toolbar with tabs + meta badges -->
        <div class="toolbar card">
          <div class="toolbar__left">
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
              :class="{ 'tab-btn--active': activeTab === 'params' }"
              type="button"
              @click="activeTab = 'params'"
            >
              {{ $t('strategyPreview.tabParams') }}
            </button>
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'code' }"
              type="button"
              @click="activeTab = 'code'"
            >
              {{ $t('strategyPreview.tabCode') }}
            </button>
          </div>
          <div class="toolbar__right">
            <span v-if="metadata.riskLevel" class="toolbar__badge" :class="`risk-tag risk-tag--${metadata.riskLevel}`">
              {{ riskLevelLabel(metadata.riskLevel) }}
            </span>
            <span v-if="metadata.timeframe" class="toolbar__badge">{{ metadata.timeframe }}</span>
            <span v-if="metadata.category" class="toolbar__badge">{{ categoryLabel(metadata.category) }}</span>
          </div>
        </div>

        <!-- Tab content -->
        <div class="tab-body card">
          <!-- Report tab -->
          <div v-if="activeTab === 'report'" class="tab-content fade-in">
            <StrategyReportCard :metadata="metadata" />
          </div>

          <!-- Params tab: editable editor + detail table side by side -->
          <div v-if="activeTab === 'params'" class="tab-content fade-in">
            <div class="params-layout">
              <div class="params-editor">
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
              <div v-if="parameters.length" class="params-detail">
                <table class="params-table">
                  <thead>
                    <tr>
                      <th>{{ $t('strategyPreview.paramKey') }}</th>
                      <th>{{ $t('strategyPreview.paramType') }}</th>
                      <th>{{ $t('strategyPreview.paramDefault') }}</th>
                      <th>{{ $t('strategyPreview.paramRange') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="param in parameters" :key="param.key">
                      <td class="mono">{{ param.key }}</td>
                      <td>{{ param.type }}</td>
                      <td>{{ param.default }}</td>
                      <td>{{ formatRange(param) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Code tab -->
          <div v-if="activeTab === 'code'" class="tab-content fade-in">
            <div v-if="codeLoading" class="code-loading">{{ $t('strategyPreview.loadingCode') }}</div>
            <div v-else-if="codeError" class="code-error">{{ codeError }}</div>
            <div v-else ref="editorContainer" class="code-editor"></div>
          </div>
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
import { computed, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
    theme: 'vs',
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

watch(activeTab, async (tab) => {
  if (tab === 'code' && rawCode.value && !editor) {
    await nextTick()
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

function riskLevelLabel(level: string): string {
  const map: Record<string, string> = {
    low: t('strategyPreview.riskLow'),
    medium: t('strategyPreview.riskMedium'),
    high: t('strategyPreview.riskHigh'),
  }
  return map[level] || level
}

function categoryLabel(category: string): string {
  const map: Record<string, string> = {
    'trend-following': t('strategyPreview.catTrendFollowing'),
    'mean-reversion': t('strategyPreview.catMeanReversion'),
    'momentum': t('strategyPreview.catMomentum'),
    'multi-indicator': t('strategyPreview.catMultiIndicator'),
    'other': t('strategyPreview.catOther'),
  }
  return map[category] || category
}

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
      codeOverride: codeDirty.value ? editedCode.value : undefined,
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
  padding-bottom: var(--spacing-xxl);
}

/* ── Header ── */
.page-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.btn--back {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
}

.header-info {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 4px;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Toolbar (tabs + badges) ── */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  border-radius: var(--radius-lg);
  gap: var(--spacing-md);
  overflow-x: auto;
}

.toolbar__left {
  display: flex;
  gap: 0;
}

.toolbar__right {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.toolbar__badge {
  padding: 3px 10px;
  font-size: var(--font-size-xs);
  font-weight: 600;
  border-radius: var(--radius-full);
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.risk-tag--low { color: #2a9d65; background: rgba(46, 125, 50, 0.08); }
.risk-tag--medium { color: #c87a00; background: rgba(200, 122, 0, 0.08); }
.risk-tag--high { color: #cf4e4e; background: rgba(207, 78, 78, 0.08); }

.tab-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
  font-family: inherit;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* ── Tab body ── */
.tab-body {
  padding: var(--spacing-lg);
  min-height: 300px;
}

.tab-content {
  min-height: 200px;
}

/* ── Params layout ── */
.params-layout {
  display: grid;
  grid-template-columns: minmax(280px, 400px) minmax(0, 1fr);
  gap: var(--spacing-xl);
  align-items: start;
}

.params-editor {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.params-detail {
  overflow-x: auto;
}

.panel-title {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-size-md);
  font-weight: 600;
}

.param-groups {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.param-group__name {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
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
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border-light);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: border-color 0.15s;
}

.field-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

/* ── Params table ── */
.params-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.params-table th {
  text-align: left;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-bottom: 2px solid var(--color-border);
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.params-table td {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.mono {
  font-family: var(--font-mono);
}

/* ── States ── */
.message {
  margin: var(--spacing-md) 0 0;
}

.error {
  color: var(--color-danger);
}

.code-loading,
.code-error {
  padding: var(--spacing-xl);
  text-align: center;
}

.code-error {
  color: var(--color-danger);
}

.code-editor {
  min-height: 480px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--color-border);
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .params-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar__right {
    flex-wrap: wrap;
  }
}
</style>
