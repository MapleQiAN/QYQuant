<template>
  <section class="ai-lab-view">
    <div class="ai-lab-shell">
      <header class="ai-lab-header">
        <div class="ai-lab-header__copy">
          <p class="ai-lab-eyebrow">{{ copy.eyebrow }}</p>
          <h1>{{ copy.title }}</h1>
          <p>{{ copy.subtitle }}</p>
        </div>

        <div class="ai-lab-header__actions">
          <span class="connection-pill" :class="connectionClass">
            <span class="status-dot"></span>
            {{ connectionLabel }}
          </span>
          <RouterLink class="btn btn-secondary" :to="{ name: 'strategy-new' }">
            {{ copy.back }}
          </RouterLink>
        </div>
      </header>

      <nav class="stage-rail" aria-label="AI strategy generation stage">
        <span
          v-for="stage in stages"
          :key="stage.key"
          class="stage-rail__item"
          :class="{ 'stage-rail__item--active': stage.key === currentStage }"
        >
          <span class="stage-rail__index">{{ stage.index }}</span>
          <span>{{ stage.label }}</span>
        </span>
      </nav>

      <div class="mobile-tabs" role="tablist" aria-label="AI Lab panels">
        <button
          v-for="tab in mobileTabs"
          :key="tab.key"
          class="mobile-tab"
          :class="{ 'mobile-tab--active': activeMobileTab === tab.key }"
          type="button"
          @click="activeMobileTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="ai-lab-grid">
        <aside class="lab-panel brief-panel" :class="mobilePanelClass('brief')">
          <div class="panel-heading">
            <p class="panel-kicker">{{ copy.briefKicker }}</p>
            <h2>{{ copy.briefTitle }}</h2>
          </div>

          <div class="mode-switch" aria-label="Strategy mode">
            <button
              v-for="mode in modes"
              :key="mode.value"
              class="mode-option"
              :class="{ 'mode-option--active': brief.mode === mode.value }"
              type="button"
              @click="brief.mode = mode.value"
            >
              <strong>{{ mode.label }}</strong>
              <span>{{ mode.description }}</span>
            </button>
          </div>

          <div class="brief-quality">
            <div>
              <span>{{ copy.briefQuality }}</span>
              <strong>{{ briefQuality.label }}</strong>
            </div>
            <div class="brief-quality__meter">
              <span
                v-for="item in 3"
                :key="item"
                :class="{ 'brief-quality__bar--active': item <= briefQuality.score }"
              ></span>
            </div>
          </div>

          <label class="field">
            <span>{{ copy.market }}</span>
            <select v-model="brief.market" class="field-control">
              <option value="crypto">Crypto</option>
              <option value="gold">Gold</option>
              <option value="stock">Stock</option>
              <option value="futures">Futures</option>
            </select>
          </label>

          <label class="field">
            <span>{{ copy.symbol }}</span>
            <input v-model.trim="brief.symbol" class="field-control" type="text" placeholder="BTCUSDT" />
          </label>

          <label class="field">
            <span>{{ copy.timeframe }}</span>
            <select v-model="brief.timeframe" class="field-control">
              <option value="1d">1d</option>
              <option value="4h">4h</option>
              <option value="1h">1h</option>
              <option value="15m">15m</option>
            </select>
          </label>

          <label class="field">
            <span>{{ copy.strategyStyle }}</span>
            <select v-model="brief.strategyStyle" class="field-control">
              <option value="trend-following">Trend following</option>
              <option value="mean-reversion">Mean reversion</option>
              <option value="momentum">Momentum</option>
              <option value="breakout">Breakout</option>
              <option value="multi-factor">Multi-factor</option>
            </select>
          </label>

          <div class="field">
            <span>{{ copy.direction }}</span>
            <div class="segmented-control">
              <button
                v-for="direction in directions"
                :key="direction.value"
                :class="{ active: brief.direction === direction.value }"
                type="button"
                @click="brief.direction = direction.value"
              >
                {{ direction.label }}
              </button>
            </div>
          </div>

          <div class="risk-grid">
            <label class="field">
              <span>{{ copy.maxDrawdown }}</span>
              <input v-model.number="brief.riskLimits.maxDrawdownPct" class="field-control" type="number" min="1" max="80" />
            </label>
            <label class="field">
              <span>{{ copy.positionRatio }}</span>
              <input v-model.number="brief.riskLimits.positionRatio" class="field-control" type="number" min="1" max="100" />
            </label>
          </div>

          <div class="field">
            <span>{{ copy.constraints }}</span>
            <div class="constraint-list">
              <button
                v-for="constraint in constraints"
                :key="constraint"
                class="constraint-chip"
                :class="{ 'constraint-chip--active': brief.constraints.includes(constraint) }"
                type="button"
                @click="toggleConstraint(constraint)"
              >
                {{ constraint }}
              </button>
            </div>
          </div>

          <label class="field">
            <span>{{ copy.notes }}</span>
            <textarea v-model.trim="brief.notes" class="field-control field-control--textarea" :placeholder="copy.notesPlaceholder"></textarea>
          </label>
        </aside>

        <main class="lab-panel console-panel" :class="mobilePanelClass('console')">
          <div class="panel-heading panel-heading--row">
            <div>
              <p class="panel-kicker">{{ copy.consoleKicker }}</p>
              <h2>{{ copy.consoleTitle }}</h2>
            </div>
            <button
              data-test="ai-lab-open-settings"
              class="btn btn-secondary"
              type="button"
              @click="openAiSettings"
            >
              {{ copy.settings }}
            </button>
          </div>

          <div v-if="aiLoadingIntegrations" class="empty-state">
            {{ copy.loadingConnection }}
          </div>

          <div v-else-if="aiIntegrations.length === 0" class="empty-state empty-state--blocked">
            <p>{{ copy.noConnectionTitle }}</p>
            <span>{{ copy.noConnectionBody }}</span>
            <button class="btn btn-primary" type="button" @click="openAiSettings">
              {{ copy.connectAction }}
            </button>
          </div>

          <template v-else>
            <label class="field connection-select">
              <span>{{ copy.aiConnection }}</span>
              <select v-model="selectedAiIntegrationId" class="field-control" data-test="ai-lab-integration">
                <option v-for="integration in aiIntegrations" :key="integration.id" :value="integration.id">
                  {{ integration.displayName }}
                </option>
              </select>
            </label>

            <div ref="consoleLog" class="research-log">
              <div v-if="aiMessages.length === 0" class="research-log__empty">
                <p>{{ copy.logEmptyTitle }}</p>
                <span>{{ copy.logEmptyBody }}</span>
              </div>

              <article
                v-for="(message, index) in aiMessages"
                :key="`${message.role}-${index}`"
                class="research-entry"
                :class="`research-entry--${message.role}`"
              >
                <div class="research-entry__meta">
                  <span>{{ message.role === 'user' ? copy.userRole : copy.aiRole }}</span>
                  <span>{{ message.role === 'assistant' ? currentStageLabel : copy.briefTitle }}</span>
                </div>
                <p>{{ message.content }}</p>
              </article>

              <article v-if="aiSubmitting" class="research-entry research-entry--assistant">
                <div class="research-entry__meta">
                  <span>{{ copy.aiRole }}</span>
                  <span>{{ copy.generating }}</span>
                </div>
                <p>{{ copy.generatingBody }}</p>
              </article>
            </div>

            <div class="quick-refine">
              <button
                v-for="hint in quickRefineHints"
                :key="hint"
                class="quick-refine__chip"
                type="button"
                @click="applyRefineHint(hint)"
              >
                {{ hint }}
              </button>
            </div>

            <label class="prompt-box">
              <span>{{ copy.promptLabel }}</span>
              <textarea
                v-model.trim="aiPrompt"
                data-test="ai-lab-prompt"
                :placeholder="copy.promptPlaceholder"
                @keydown.ctrl.enter.prevent="handleGenerate"
              ></textarea>
            </label>

            <p v-if="aiError" class="form-message error">{{ aiError }}</p>

            <div class="console-actions">
              <button
                data-test="ai-lab-generate"
                class="btn btn-primary"
                type="button"
                :disabled="aiSubmitting || !selectedAiIntegrationId"
                @click="handleGenerate"
              >
                <span v-if="aiSubmitting" class="btn-spinner"></span>
                {{ aiSubmitting ? copy.generating : copy.generateAction }}
              </button>
            </div>
          </template>
        </main>

        <aside class="lab-panel draft-panel" :class="mobilePanelClass('draft')">
          <div class="panel-heading">
            <p class="panel-kicker">{{ copy.draftKicker }}</p>
            <h2>{{ copy.draftTitle }}</h2>
          </div>

          <div v-if="!aiLatestAnalysis" class="draft-placeholder">
            <p>{{ copy.noDraftTitle }}</p>
            <span>{{ copy.noDraftBody }}</span>
          </div>

          <template v-else>
            <div class="draft-status" :class="`draft-status--${validationState}`">
              <span class="status-dot"></span>
              <strong>{{ validationLabel }}</strong>
            </div>

            <div class="summary-card">
              <div>
                <span>{{ copy.name }}</span>
                <strong>{{ metadataText('name') }}</strong>
              </div>
              <div>
                <span>{{ copy.symbol }}</span>
                <strong>{{ metadataText('symbol') }}</strong>
              </div>
              <div>
                <span>{{ copy.timeframe }}</span>
                <strong>{{ metadataText('timeframe') }}</strong>
              </div>
              <div>
                <span>{{ copy.riskLevel }}</span>
                <strong>{{ riskLevelLabel(metadataText('riskLevel')) }}</strong>
              </div>
            </div>

            <section v-if="metadataText('logicExplanation') !== '-'" class="draft-section">
              <h3>{{ copy.logic }}</h3>
              <p>{{ metadataText('logicExplanation') }}</p>
            </section>

            <section v-if="metadataText('riskRules') !== '-'" class="draft-section">
              <h3>{{ copy.riskRules }}</h3>
              <p>{{ metadataText('riskRules') }}</p>
            </section>

            <section class="draft-section">
              <h3>{{ copy.parameters }}</h3>
              <div v-if="aiLatestAnalysis.parameterCandidates.length" class="parameter-table">
                <div class="parameter-table__row parameter-table__row--head">
                  <span>{{ copy.paramName }}</span>
                  <span>{{ copy.paramDefault }}</span>
                </div>
                <div
                  v-for="param in aiLatestAnalysis.parameterCandidates"
                  :key="param.key"
                  class="parameter-table__row"
                >
                  <span>{{ parameterLabel(param) }}</span>
                  <strong>{{ String(param.default ?? '-') }}</strong>
                </div>
              </div>
              <p v-else class="muted-copy">{{ copy.noParams }}</p>
            </section>

            <section class="draft-section">
              <h3>{{ copy.validation }}</h3>
              <div class="validation-list">
                <div class="validation-item">
                  <span>{{ copy.entrypoint }}</span>
                  <strong :class="validationClass(hasEntrypoint)">{{ hasEntrypoint ? copy.pass : copy.warn }}</strong>
                </div>
                <div class="validation-item">
                  <span>{{ copy.parameters }}</span>
                  <strong class="validation-state validation-state--pass">{{ aiLatestAnalysis.parameterCandidates.length }}</strong>
                </div>
                <div class="validation-item">
                  <span>{{ copy.errors }}</span>
                  <strong :class="validationClass(aiLatestAnalysis.errors.length === 0)">
                    {{ aiLatestAnalysis.errors.length }}
                  </strong>
                </div>
              </div>
            </section>

            <div v-if="aiLatestAnalysis.warnings.length" class="summary-alert summary-alert--warning">
              {{ aiLatestAnalysis.warnings.join(', ') }}
            </div>
            <div v-if="aiLatestAnalysis.errors.length" class="summary-alert summary-alert--error">
              {{ aiLatestAnalysis.errors.join(', ') }}
            </div>

            <div class="draft-actions">
              <button
                data-test="ai-lab-adopt"
                class="btn btn-primary"
                type="button"
                :disabled="!aiCanAdopt"
                @click="adoptAiDraft"
              >
                {{ adoptLabel }}
              </button>
              <button class="btn btn-secondary" type="button" @click="applyRefineHint(copy.refineMore)">
                {{ copy.refineAction }}
              </button>
            </div>
          </template>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import { fetchIntegrations, type UserIntegration } from '../api/integrations'
import { generateAiStrategyDraft } from '../api/strategies'
import type { AiStrategyMessage, StrategyImportAnalysis, StrategyParameter } from '../types/Strategy'

type StrategyMode = 'guided' | 'mixed' | 'expert'
type GenerationStage = 'brief' | 'clarify' | 'design' | 'validate' | 'package'
type MobileTab = 'brief' | 'console' | 'draft'
type ValidationState = 'pass' | 'warn' | 'block'

interface StrategyBriefState {
  mode: StrategyMode
  market: string
  symbol: string
  timeframe: string
  strategyStyle: string
  direction: string
  riskLimits: {
    maxDrawdownPct: number
    positionRatio: number
  }
  constraints: string[]
  notes: string
}

const { locale } = useI18n()
const router = useRouter()

const copy = computed(() => {
  const zh = String(locale.value || '').startsWith('zh')
  return zh
    ? {
        eyebrow: 'AI 策略引擎',
        title: 'AI Strategy Lab',
        subtitle: '把交易想法拆成可验证的策略草案，再进入预览、导入和回测。',
        back: '返回新建策略',
        briefKicker: 'Strategy Brief',
        briefTitle: '策略意图',
        briefQuality: '简报质量',
        market: '市场',
        symbol: '标的',
        timeframe: '周期',
        strategyStyle: '策略风格',
        direction: '方向',
        maxDrawdown: '最大回撤 %',
        positionRatio: '仓位比例 %',
        constraints: '约束',
        notes: '补充说明',
        notesPlaceholder: '例如：只做多，避免高频，突破后等待确认，不使用未来数据。',
        consoleKicker: 'AI Research Console',
        consoleTitle: '研究控制台',
        settings: 'AI 设置',
        loadingConnection: '正在加载 AI 连接...',
        noConnectionTitle: '需要先配置 AI 连接',
        noConnectionBody: '在设置页保存 OpenAI Compatible 连接后，即可生成策略草案。',
        connectAction: '去设置',
        aiConnection: 'AI 连接',
        logEmptyTitle: '从策略意图开始',
        logEmptyBody: '左侧结构化简报会和你的补充描述一起发送给 AI。',
        userRole: '你',
        aiRole: 'AI',
        generating: '生成中',
        generatingBody: '正在生成策略逻辑、参数和验证信息。',
        promptLabel: '补充描述',
        promptPlaceholder: '描述你的市场假设、信号、过滤器或想优化的风险点。Ctrl+Enter 生成。',
        generateAction: '生成可验证草案',
        draftKicker: 'Verified Draft',
        draftTitle: '可验证草案',
        noDraftTitle: '暂无草案',
        noDraftBody: '生成后会在这里展示摘要、参数、验证状态和风险警告。',
        name: '名称',
        riskLevel: '风险等级',
        logic: '策略逻辑',
        riskRules: '风控规则',
        parameters: '参数',
        paramName: '参数',
        paramDefault: '默认值',
        noParams: '未识别到参数。',
        validation: '验证',
        entrypoint: '入口函数',
        errors: '错误',
        pass: '通过',
        warn: '待复核',
        adopt: '采用草案',
        adoptWithWarning: '带警告采用',
        blocked: '修复阻塞项',
        refineAction: '继续优化',
        refineMore: '继续优化这份草案，优先降低回撤并解释修改原因。',
      }
    : {
        eyebrow: 'AI Strategy Engine',
        title: 'AI Strategy Lab',
        subtitle: 'Turn a market thesis into a verifiable draft before preview, import, and backtest.',
        back: 'Back to creation',
        briefKicker: 'Strategy Brief',
        briefTitle: 'Strategy intent',
        briefQuality: 'Brief quality',
        market: 'Market',
        symbol: 'Symbol',
        timeframe: 'Timeframe',
        strategyStyle: 'Strategy style',
        direction: 'Direction',
        maxDrawdown: 'Max drawdown %',
        positionRatio: 'Position ratio %',
        constraints: 'Constraints',
        notes: 'Notes',
        notesPlaceholder: 'Example: long only, avoid high frequency, confirm breakouts, no look-ahead data.',
        consoleKicker: 'AI Research Console',
        consoleTitle: 'Research console',
        settings: 'AI settings',
        loadingConnection: 'Loading AI connections...',
        noConnectionTitle: 'AI connection required',
        noConnectionBody: 'Save an OpenAI Compatible connection in Settings before generating a strategy draft.',
        connectAction: 'Open settings',
        aiConnection: 'AI connection',
        logEmptyTitle: 'Start from the strategy brief',
        logEmptyBody: 'The structured brief and your extra notes will be sent to AI together.',
        userRole: 'You',
        aiRole: 'AI',
        generating: 'Generating',
        generatingBody: 'Generating strategy logic, parameters, and validation details.',
        promptLabel: 'Additional prompt',
        promptPlaceholder: 'Describe market thesis, signals, filters, or risk changes. Ctrl+Enter to generate.',
        generateAction: 'Generate verified draft',
        draftKicker: 'Verified Draft',
        draftTitle: 'Verifiable draft',
        noDraftTitle: 'No draft yet',
        noDraftBody: 'After generation, summary, parameters, validation, and risk warnings appear here.',
        name: 'Name',
        riskLevel: 'Risk level',
        logic: 'Strategy logic',
        riskRules: 'Risk rules',
        parameters: 'Parameters',
        paramName: 'Parameter',
        paramDefault: 'Default',
        noParams: 'No parameters detected.',
        validation: 'Validation',
        entrypoint: 'Entrypoint',
        errors: 'Errors',
        pass: 'Pass',
        warn: 'Review',
        adopt: 'Adopt draft',
        adoptWithWarning: 'Adopt with warnings',
        blocked: 'Fix blockers',
        refineAction: 'Refine',
        refineMore: 'Refine this draft with lower drawdown first, and explain what changed.',
      }
})

const modes = [
  { value: 'guided' as const, label: 'Guided', description: 'AI asks for missing inputs' },
  { value: 'mixed' as const, label: 'Mixed', description: 'AI plus manual constraints' },
  { value: 'expert' as const, label: 'Expert', description: 'Direct control of assumptions' },
]

const directions = [
  { value: 'long-only', label: 'Long' },
  { value: 'short-only', label: 'Short' },
  { value: 'long-short', label: 'L/S' },
]

const stages = [
  { key: 'brief' as const, index: '01', label: 'Brief' },
  { key: 'clarify' as const, index: '02', label: 'Clarify' },
  { key: 'design' as const, index: '03', label: 'Design' },
  { key: 'validate' as const, index: '04', label: 'Validate' },
  { key: 'package' as const, index: '05', label: 'Package' },
]

const mobileTabs = [
  { key: 'brief' as const, label: 'Brief' },
  { key: 'console' as const, label: 'Console' },
  { key: 'draft' as const, label: 'Draft' },
]

const constraints = ['No leverage', 'Long only', 'No high frequency', 'Stop loss required', 'Explainable rules', 'Low turnover']
const quickRefineHints = ['Lower drawdown', 'Add stop loss', 'Reduce trade frequency', 'Use daily timeframe', 'Tighten parameter bounds']

const brief = reactive<StrategyBriefState>({
  mode: 'guided',
  market: 'crypto',
  symbol: 'BTCUSDT',
  timeframe: '1d',
  strategyStyle: 'trend-following',
  direction: 'long-only',
  riskLimits: {
    maxDrawdownPct: 15,
    positionRatio: 30,
  },
  constraints: ['No leverage', 'Stop loss required', 'Explainable rules'],
  notes: '',
})

const activeMobileTab = ref<MobileTab>('console')
const aiLoadingIntegrations = ref(false)
const aiIntegrations = ref<UserIntegration[]>([])
const selectedAiIntegrationId = ref('')
const aiMessages = ref<AiStrategyMessage[]>([])
const aiPrompt = ref('')
const aiSubmitting = ref(false)
const aiError = ref('')
const aiLatestAnalysis = ref<StrategyImportAnalysis | null>(null)
const consoleLog = ref<HTMLElement | null>(null)

const briefQuality = computed(() => {
  let score = 0
  if (brief.symbol && brief.market && brief.timeframe) score += 1
  if (brief.strategyStyle && brief.direction && brief.constraints.length >= 2) score += 1
  if (brief.notes || brief.riskLimits.maxDrawdownPct || brief.riskLimits.positionRatio) score += 1
  const labels = ['Incomplete', 'Enough for draft', 'Strong brief']
  return { score, label: labels[Math.max(0, score - 1)] ?? labels[0] }
})

const currentStage = computed<GenerationStage>(() => {
  if (aiSubmitting.value) return 'design'
  if (!aiLatestAnalysis.value && aiMessages.value.length > 0) return 'clarify'
  if (!aiLatestAnalysis.value) return 'brief'
  if (validationState.value === 'block') return 'validate'
  return 'package'
})

const currentStageLabel = computed(() => stages.find((stage) => stage.key === currentStage.value)?.label ?? 'AI')

const hasEntrypoint = computed(() => (aiLatestAnalysis.value?.entrypointCandidates.length ?? 0) > 0)

const validationState = computed<ValidationState>(() => {
  const analysis = aiLatestAnalysis.value
  if (!analysis) return 'warn'
  if (!hasEntrypoint.value || analysis.errors.length > 0) return 'block'
  if (analysis.warnings.length > 0) return 'warn'
  return 'pass'
})

const aiCanAdopt = computed(() => {
  const analysis = aiLatestAnalysis.value
  return Boolean(analysis?.draftImportId && validationState.value !== 'block')
})

const validationLabel = computed(() => {
  if (validationState.value === 'pass') return copy.value.pass
  if (validationState.value === 'warn') return copy.value.warn
  return copy.value.blocked
})

const adoptLabel = computed(() => {
  if (validationState.value === 'block') return copy.value.blocked
  if (validationState.value === 'warn') return copy.value.adoptWithWarning
  return copy.value.adopt
})

const connectionLabel = computed(() => {
  if (aiLoadingIntegrations.value) return copy.value.loadingConnection
  if (aiIntegrations.value.length === 0) return copy.value.noConnectionTitle
  const active = aiIntegrations.value.find((item) => item.id === selectedAiIntegrationId.value)
  return active?.displayName || copy.value.aiConnection
})

const connectionClass = computed(() => ({
  'connection-pill--loading': aiLoadingIntegrations.value,
  'connection-pill--blocked': !aiLoadingIntegrations.value && aiIntegrations.value.length === 0,
  'connection-pill--ready': !aiLoadingIntegrations.value && aiIntegrations.value.length > 0,
}))

function mobilePanelClass(tab: MobileTab) {
  return { 'lab-panel--mobile-hidden': activeMobileTab.value !== tab }
}

function toggleConstraint(constraint: string) {
  const index = brief.constraints.indexOf(constraint)
  if (index >= 0) {
    brief.constraints.splice(index, 1)
  } else {
    brief.constraints.push(constraint)
  }
}

function compileBriefMessage(): string {
  const lines = [
    'Create a QYQuant executable strategy draft from this structured brief.',
    `Mode: ${brief.mode}`,
    `Market: ${brief.market}`,
    `Symbol: ${brief.symbol}`,
    `Timeframe: ${brief.timeframe}`,
    `Style: ${brief.strategyStyle}`,
    `Direction: ${brief.direction}`,
    `Risk: max drawdown ${brief.riskLimits.maxDrawdownPct}%, position ratio ${brief.riskLimits.positionRatio}%`,
    `Constraints: ${brief.constraints.join(', ') || 'none'}`,
  ]
  if (brief.notes) lines.push(`User notes: ${brief.notes}`)
  if (aiPrompt.value) lines.push(`Additional request: ${aiPrompt.value}`)
  lines.push('Return strategy code, metadata, parameter definitions, assumptions, and validation warnings if any.')
  return lines.join('\n')
}

async function loadAiIntegrations() {
  aiLoadingIntegrations.value = true
  aiError.value = ''
  try {
    const integrations = await fetchIntegrations()
    aiIntegrations.value = integrations.filter((item) => item.providerKey === 'openai_compatible')
    if (!selectedAiIntegrationId.value && aiIntegrations.value.length > 0) {
      selectedAiIntegrationId.value = aiIntegrations.value[0].id
    }
  } catch (error: any) {
    aiError.value = error?.message || 'Failed to load AI connections'
  } finally {
    aiLoadingIntegrations.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (consoleLog.value) {
    consoleLog.value.scrollTop = consoleLog.value.scrollHeight
  }
}

async function handleGenerate() {
  if (!selectedAiIntegrationId.value || aiSubmitting.value) {
    return
  }

  const message = compileBriefMessage()
  const pendingMessages: AiStrategyMessage[] = [...aiMessages.value, { role: 'user', content: message }]
  const previousPrompt = aiPrompt.value

  aiSubmitting.value = true
  aiError.value = ''
  aiMessages.value = pendingMessages
  aiPrompt.value = ''
  await scrollToBottom()

  try {
    const result = await generateAiStrategyDraft({
      integrationId: selectedAiIntegrationId.value,
      messages: pendingMessages,
    })
    aiMessages.value = [...pendingMessages, { role: 'assistant', content: result.reply }]
    aiLatestAnalysis.value = result.analysis
    activeMobileTab.value = result.analysis ? 'draft' : 'console'
    await scrollToBottom()
  } catch (error: any) {
    aiPrompt.value = previousPrompt
    aiError.value = error?.message || 'Failed to generate AI strategy draft'
  } finally {
    aiSubmitting.value = false
  }
}

async function adoptAiDraft() {
  const analysis = aiLatestAnalysis.value
  if (!analysis?.draftImportId || validationState.value === 'block') {
    return
  }
  sessionStorage.setItem(`strategy-import:${analysis.draftImportId}`, JSON.stringify(analysis))
  await router.push({
    name: 'strategy-preview',
    query: {
      draftImportId: analysis.draftImportId,
      source: 'ai',
    },
  })
}

function openAiSettings() {
  router.push({
    path: '/settings',
    query: {
      provider: 'openai_compatible',
      redirect: '/strategies/ai-lab',
    },
  })
}

function applyRefineHint(hint: string) {
  aiPrompt.value = hint
  activeMobileTab.value = 'console'
}

function metadataText(key: string): string {
  const value = aiLatestAnalysis.value?.metadataCandidates?.[key]
  if (typeof value === 'string' && value.trim()) return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return '-'
}

function riskLevelLabel(level: string): string {
  const map: Record<string, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
  }
  return map[level] || level
}

function parameterLabel(param: StrategyParameter): string {
  const userFacing = param.user_facing
  if (userFacing && typeof userFacing === 'object' && 'label' in userFacing && typeof userFacing.label === 'string') {
    return userFacing.label
  }
  return param.key
}

function validationClass(value: boolean) {
  return value ? 'validation-state validation-state--pass' : 'validation-state validation-state--warn'
}

onMounted(() => {
  void loadAiIntegrations()
})
</script>

<style scoped>
.ai-lab-view {
  width: 100%;
}

.ai-lab-shell {
  max-width: 1760px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg) var(--spacing-xl);
}

.ai-lab-header,
.panel-heading--row,
.ai-lab-header__actions,
.stage-rail,
.mobile-tabs,
.console-actions,
.draft-actions {
  display: flex;
  align-items: center;
}

.ai-lab-header {
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.ai-lab-header__copy,
.panel-heading,
.research-log__empty,
.draft-placeholder,
.empty-state {
  display: grid;
  gap: var(--spacing-xs);
}

.ai-lab-header h1 {
  margin: 0;
  font-size: clamp(28px, 4vw, 48px);
  line-height: 1;
  letter-spacing: 0;
}

.ai-lab-header p,
.panel-heading h2,
.panel-heading p,
.research-entry p,
.draft-section h3,
.draft-section p,
.muted-copy,
.empty-state p,
.empty-state span,
.draft-placeholder p,
.draft-placeholder span {
  margin: 0;
}

.ai-lab-eyebrow,
.panel-kicker {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.ai-lab-header__actions {
  justify-content: flex-end;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.connection-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 6px 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-warning);
}

.connection-pill--ready .status-dot,
.draft-status--pass .status-dot {
  background: var(--color-success);
}

.connection-pill--blocked .status-dot,
.draft-status--block .status-dot {
  background: var(--color-danger);
}

.stage-rail {
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-xs);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  overflow-x: auto;
}

.stage-rail__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: max-content;
  padding: 8px 12px;
  border-radius: var(--radius-xs);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.stage-rail__item--active {
  background: var(--color-primary-bg);
  color: var(--color-text-primary);
}

.stage-rail__index {
  font-family: var(--font-mono);
  color: var(--color-accent);
}

.ai-lab-grid {
  display: grid;
  grid-template-columns: minmax(280px, 330px) minmax(460px, 1fr) minmax(340px, 410px);
  gap: var(--spacing-md);
  align-items: start;
}

.lab-panel {
  min-width: 0;
  min-height: 680px;
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.brief-panel,
.draft-panel {
  display: grid;
  gap: var(--spacing-md);
}

.console-panel {
  display: grid;
  gap: var(--spacing-md);
}

.panel-heading {
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--color-border-light);
}

.panel-heading--row {
  justify-content: space-between;
  gap: var(--spacing-md);
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-xs);
}

.mode-option {
  min-width: 0;
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  text-align: left;
  cursor: pointer;
}

.mode-option strong,
.mode-option span {
  display: block;
}

.mode-option strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.mode-option span {
  margin-top: 3px;
  font-size: var(--font-size-xs);
  line-height: 1.35;
}

.mode-option--active {
  border-color: var(--color-border);
  background: var(--color-accent-bg);
}

.brief-quality {
  display: grid;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface-elevated);
}

.brief-quality > div:first-child,
.summary-card > div,
.validation-item,
.draft-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.brief-quality span,
.summary-card span,
.validation-item span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.brief-quality__meter {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.brief-quality__meter span {
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-border-light);
}

.brief-quality__meter .brief-quality__bar--active {
  background: var(--color-accent);
}

.field,
.prompt-box {
  display: grid;
  gap: 6px;
}

.field > span,
.prompt-box > span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.field-control,
.prompt-box textarea {
  width: 100%;
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font: inherit;
}

.field-control {
  min-height: 38px;
  padding: 8px 10px;
}

.field-control:focus,
.prompt-box textarea:focus {
  border-color: var(--color-border);
  outline: none;
}

.field-control--textarea,
.prompt-box textarea {
  min-height: 110px;
  padding: 10px 12px;
  resize: vertical;
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.segmented-control,
.constraint-list,
.quick-refine {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.segmented-control button,
.constraint-chip,
.quick-refine__chip,
.mobile-tab {
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-xs);
  font-weight: 800;
}

.segmented-control button {
  flex: 1;
  min-height: 34px;
}

.constraint-chip,
.quick-refine__chip {
  padding: 6px 10px;
}

.segmented-control button.active,
.constraint-chip--active,
.quick-refine__chip:hover,
.mobile-tab--active {
  border-color: var(--color-border);
  background: var(--color-accent);
  color: var(--color-text-primary);
}

.empty-state {
  min-height: 460px;
  place-items: center;
  text-align: center;
  border: 2px dashed var(--color-border-light);
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
}

.empty-state p,
.draft-placeholder p,
.research-log__empty p {
  color: var(--color-text-primary);
  font-weight: 800;
}

.empty-state--blocked {
  padding: var(--spacing-xl);
}

.connection-select {
  max-width: 360px;
}

.research-log {
  min-height: 360px;
  max-height: 520px;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  background:
    linear-gradient(180deg, rgba(25, 118, 210, 0.04), transparent 28%),
    var(--color-surface-elevated);
}

.research-log__empty {
  min-height: 320px;
  place-items: center;
  text-align: center;
}

.research-entry {
  display: grid;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface);
}

.research-entry--assistant {
  border-color: var(--color-primary-border);
}

.research-entry--user {
  border-color: rgba(249, 168, 37, 0.45);
}

.research-entry__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
}

.research-entry p {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.65;
}

.prompt-box textarea {
  min-height: 116px;
}

.console-actions,
.draft-actions {
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: var(--radius-full);
  border: 2px solid rgba(17, 17, 17, 0.25);
  border-top-color: var(--color-text-primary);
  animation: spin 0.8s linear infinite;
}

.form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.error {
  color: var(--color-danger);
}

.draft-placeholder {
  min-height: 520px;
  place-items: center;
  text-align: center;
  border: 2px dashed var(--color-border-light);
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
}

.draft-status {
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface-elevated);
}

.draft-status--pass {
  border-color: rgba(46, 125, 50, 0.35);
}

.draft-status--warn {
  border-color: rgba(230, 81, 0, 0.35);
}

.draft-status--block {
  border-color: rgba(212, 57, 59, 0.35);
}

.summary-card,
.draft-section {
  display: grid;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
  background: var(--color-surface-elevated);
}

.summary-card strong,
.parameter-table strong,
.validation-item strong {
  font-family: var(--font-mono);
}

.draft-section h3 {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.draft-section p,
.muted-copy {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.parameter-table {
  display: grid;
  gap: 4px;
}

.parameter-table__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-sm);
  padding: 7px 0;
  border-top: 1px solid var(--color-border-light);
}

.parameter-table__row--head {
  border-top: none;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  text-transform: uppercase;
}

.validation-list {
  display: grid;
  gap: var(--spacing-xs);
}

.validation-state--pass {
  color: var(--color-success);
}

.validation-state--warn {
  color: var(--color-warning);
}

.summary-alert {
  padding: var(--spacing-sm);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.summary-alert--warning {
  border: 2px solid rgba(230, 81, 0, 0.25);
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.summary-alert--error {
  border: 2px solid rgba(212, 57, 59, 0.25);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.mobile-tabs {
  display: none;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.mobile-tab {
  flex: 1;
  min-height: 36px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .ai-lab-grid {
    grid-template-columns: 1fr;
  }

  .mobile-tabs {
    display: flex;
  }

  .lab-panel {
    min-height: auto;
  }

  .lab-panel--mobile-hidden {
    display: none;
  }
}

@media (max-width: 720px) {
  .ai-lab-shell {
    padding: 0 var(--spacing-md) var(--spacing-lg);
  }

  .ai-lab-header,
  .ai-lab-header__actions,
  .panel-heading--row {
    align-items: stretch;
    flex-direction: column;
  }

  .mode-switch,
  .risk-grid {
    grid-template-columns: 1fr;
  }

  .stage-rail__item {
    padding: 7px 10px;
  }
}
</style>
