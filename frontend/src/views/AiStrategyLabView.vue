<template>
  <section class="ai-lab-view">
    <!-- Ambient background -->
    <div class="ai-lab-ambient" aria-hidden="true">
      <div class="ai-lab-ambient__grid"></div>
      <div class="ai-lab-ambient__glow ai-lab-ambient__glow--left"></div>
      <div class="ai-lab-ambient__glow ai-lab-ambient__glow--right"></div>
    </div>

    <div class="ai-lab-shell">
      <header class="ai-lab-header">
        <div class="ai-lab-header__copy">
          <div class="ai-lab-eyebrow-row">
            <span class="ai-lab-eyebrow">{{ copy.eyebrow }}</span>
            <span class="ai-lab-header__divider"></span>
            <span class="connection-pill" :class="connectionClass">
              <span class="status-dot"></span>
              {{ connectionLabel }}
            </span>
          </div>
          <h1>{{ copy.title }}</h1>
          <p>{{ copy.subtitle }}</p>
        </div>

        <div class="ai-lab-header__actions">
          <button v-if="!historyOpen" class="btn btn-ghost" type="button" @click="historyOpen = true">
            {{ copy.historyTitle }}
          </button>
          <RouterLink class="btn btn-ghost" :to="{ name: 'strategy-new' }">
            {{ copy.back }}
          </RouterLink>
        </div>
      </header>

      <nav class="stage-rail" aria-label="AI strategy generation stage">
        <div class="stage-rail__track">
          <span
            v-for="(stage, idx) in stages"
            :key="stage.key"
            class="stage-rail__item"
            :class="{
              'stage-rail__item--active': stage.key === currentStage,
              'stage-rail__item--done': stageDone(idx)
            }"
          >
            <span class="stage-rail__dot">
              <span class="stage-rail__dot-inner"></span>
            </span>
            <span class="stage-rail__label">{{ stage.label }}</span>
            <span v-if="idx < stages.length - 1" class="stage-rail__line"></span>
          </span>
        </div>
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

      <div class="ai-lab-grid" :class="{ 'ai-lab-grid--history-open': historyOpen }">
        <aside v-if="historyOpen" class="lab-panel history-panel">
          <div class="panel-heading">
            <div class="panel-heading--row">
              <div>
                <p class="panel-kicker">{{ copy.historyTitle }}</p>
                <h2>{{ copy.historyTitle }}</h2>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="historyOpen = false" aria-label="Close history">&times;</button>
            </div>
          </div>

          <button class="history-new-btn" type="button" @click="startNewSession">
            {{ copy.newSession }}
          </button>

          <div v-if="!historyLoaded" class="history-loading">{{ copy.generating }}</div>

          <div v-else-if="sessions.length === 0" class="history-empty">
            <span>{{ copy.logEmptyBody }}</span>
          </div>

          <ul v-else class="history-list">
            <li
              v-for="session in sessions"
              :key="session.id"
              class="history-item"
              :class="{ 'history-item--active': session.id === activeSessionId }"
            >
              <button class="history-item__body" type="button" @click="loadSession(session.id)">
                <strong class="history-item__title">{{ session.title || copy.newSession }}</strong>
                <span class="history-item__meta">{{ copy.messageCount.replace('{n}', String(session.messageCount)) }}</span>
              </button>
              <button class="history-item__delete" type="button" @click.stop="handleDeleteSession(session.id)" aria-label="Delete">&times;</button>
            </li>
          </ul>
        </aside>

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
              <option value="crypto">{{ t('aiLab.marketCrypto') }}</option>
              <option value="gold">{{ t('aiLab.marketGold') }}</option>
              <option value="stock">{{ t('aiLab.marketStock') }}</option>
              <option value="futures">{{ t('aiLab.marketFutures') }}</option>
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
              <option value="trend-following">{{ t('aiLab.styleTrendFollowing') }}</option>
              <option value="mean-reversion">{{ t('aiLab.styleMeanReversion') }}</option>
              <option value="momentum">{{ t('aiLab.styleMomentum') }}</option>
              <option value="breakout">{{ t('aiLab.styleBreakout') }}</option>
              <option value="multi-factor">{{ t('aiLab.styleMultiFactor') }}</option>
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
                v-for="item in constraintList"
                :key="item.key"
                class="constraint-chip"
                :class="{ 'constraint-chip--active': brief.constraints.includes(item.key) }"
                type="button"
                @click="toggleConstraint(item.key)"
              >
                {{ item.label }}
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
                :key="hint.key"
                class="quick-refine__chip"
                type="button"
                @click="applyRefineHint(hint.label)"
              >
                {{ hint.label }}
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

            <div v-if="qsgaStatus" class="qsga-status">
              <span>{{ copy.qsgaStatus }}</span>
              <strong>{{ qsgaStatusLabel }}</strong>
            </div>

            <div
              v-if="qsgaTrustNotice"
              class="summary-alert"
              :class="qsgaTrustPassed ? 'summary-alert--success' : 'summary-alert--warning'"
              data-test="ai-lab-trust-notice"
            >
              {{ qsgaTrustNotice }}
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

            <section v-if="qsgaVerificationEntries.length" class="draft-section">
              <h3>{{ copy.verificationChain }}</h3>
              <div class="validation-list">
                <div
                  v-for="item in qsgaVerificationEntries"
                  :key="item.key"
                  class="validation-item"
                >
                  <span>{{ item.label }}</span>
                  <strong :class="verificationStatusClass(item.status)">{{ item.status }}</strong>
                </div>
              </div>
              <div v-if="qsgaMessages.length" class="summary-alert" :class="validationState === 'block' ? 'summary-alert--error' : 'summary-alert--warning'">
                {{ qsgaMessages.join(', ') }}
              </div>
            </section>

            <section v-if="qyirPreview" class="draft-section">
              <h3>{{ copy.qyirTitle }}</h3>
              <pre class="qyir-preview">{{ qyirPreview }}</pre>
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
import { deleteAiSession, generateAiStrategyDraft, getAiSession, listAiSessions } from '../api/strategies'
import { useUserStore } from '../stores/user'
import type { AiSessionSummary, AiStrategyMessage, StrategyImportAnalysis, StrategyParameter } from '../types/Strategy'

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

const { t, locale } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const isZh = computed(() => (userStore.locale || locale.value) === 'zh')

const copy = computed(() => ({
  eyebrow: t('aiLab.eyebrow'),
  title: t('aiLab.title'),
  subtitle: t('aiLab.subtitle'),
  back: t('aiLab.back'),
  briefKicker: t('aiLab.briefKicker'),
  briefTitle: t('aiLab.briefTitle'),
  briefQuality: t('aiLab.briefQuality'),
  market: t('aiLab.market'),
  symbol: t('aiLab.symbol'),
  timeframe: t('aiLab.timeframe'),
  strategyStyle: t('aiLab.strategyStyle'),
  direction: t('aiLab.direction'),
  maxDrawdown: t('aiLab.maxDrawdown'),
  positionRatio: t('aiLab.positionRatio'),
  constraints: t('aiLab.constraints'),
  notes: t('aiLab.notes'),
  notesPlaceholder: t('aiLab.notesPlaceholder'),
  consoleKicker: t('aiLab.consoleKicker'),
  consoleTitle: t('aiLab.consoleTitle'),
  settings: t('aiLab.settings'),
  loadingConnection: t('aiLab.loadingConnection'),
  noConnectionTitle: t('aiLab.noConnectionTitle'),
  noConnectionBody: t('aiLab.noConnectionBody'),
  connectAction: t('aiLab.connectAction'),
  aiConnection: t('aiLab.aiConnection'),
  logEmptyTitle: t('aiLab.logEmptyTitle'),
  logEmptyBody: t('aiLab.logEmptyBody'),
  userRole: t('aiLab.userRole'),
  aiRole: t('aiLab.aiRole'),
  generating: t('aiLab.generating'),
  generatingBody: t('aiLab.generatingBody'),
  promptLabel: t('aiLab.promptLabel'),
  promptPlaceholder: t('aiLab.promptPlaceholder'),
  generateAction: t('aiLab.generateAction'),
  draftKicker: t('aiLab.draftKicker'),
  draftTitle: t('aiLab.draftTitle'),
  noDraftTitle: t('aiLab.noDraftTitle'),
  noDraftBody: t('aiLab.noDraftBody'),
  name: t('aiLab.name'),
  riskLevel: t('aiLab.riskLevel'),
  logic: t('aiLab.logic'),
  riskRules: t('aiLab.riskRules'),
  parameters: t('aiLab.parameters'),
  paramName: t('aiLab.paramName'),
  paramDefault: t('aiLab.paramDefault'),
  noParams: t('aiLab.noParams'),
  validation: t('aiLab.validation'),
  entrypoint: t('aiLab.entrypoint'),
  errors: t('aiLab.errors'),
  pass: t('aiLab.pass'),
  warn: t('aiLab.warn'),
  adopt: t('aiLab.adopt'),
  adoptWithWarning: t('aiLab.adoptWithWarning'),
  blocked: t('aiLab.blocked'),
  qsgaStatus: t('aiLab.qsgaStatus'),
  qsgaDraftReady: t('aiLab.qsgaDraftReady'),
  qsgaRunning: t('aiLab.qsgaRunning'),
  qsgaClarification: t('aiLab.qsgaClarification'),
  qsgaRejected: t('aiLab.qsgaRejected'),
  qsgaBlocked: t('aiLab.qsgaBlocked'),
  qsgaTrusted: t('aiLab.qsgaTrusted'),
  qsgaTrustPending: t('aiLab.qsgaTrustPending'),
  qsgaTrustBlocked: t('aiLab.qsgaTrustBlocked'),
  verificationChain: t('aiLab.verificationChain'),
  qyirTitle: t('aiLab.qyirTitle'),
  refineAction: t('aiLab.refineAction'),
  refineMore: t('aiLab.refineMore'),
  historyTitle: t('aiLab.historyTitle'),
  newSession: t('aiLab.newSession'),
  messageCount: t('aiLab.messageCount'),
  deleteConfirm: t('aiLab.deleteConfirm'),
  loadError: t('aiLab.loadError'),
  deleteError: t('aiLab.deleteError'),
}))

const modes = computed(() => [
  { value: 'guided' as const, label: t('aiLab.modeGuided'), description: t('aiLab.modeGuidedDesc') },
  { value: 'mixed' as const, label: t('aiLab.modeMixed'), description: t('aiLab.modeMixedDesc') },
  { value: 'expert' as const, label: t('aiLab.modeExpert'), description: t('aiLab.modeExpertDesc') },
])

const directions = computed(() => [
  { value: 'long-only', label: t('aiLab.directionLong') },
  { value: 'short-only', label: t('aiLab.directionShort') },
  { value: 'long-short', label: t('aiLab.directionLongShort') },
])

const stages = computed(() => [
  { key: 'brief' as const, index: '01', label: t('aiLab.stageBrief') },
  { key: 'clarify' as const, index: '02', label: t('aiLab.stageClarify') },
  { key: 'design' as const, index: '03', label: t('aiLab.stageDesign') },
  { key: 'validate' as const, index: '04', label: t('aiLab.stageValidate') },
  { key: 'package' as const, index: '05', label: t('aiLab.stagePackage') },
])

const mobileTabs = computed(() => [
  { key: 'brief' as const, label: t('aiLab.mobileTabBrief') },
  { key: 'console' as const, label: t('aiLab.mobileTabConsole') },
  { key: 'draft' as const, label: t('aiLab.mobileTabDraft') },
])

const constraintKeys = ['constraintNoLeverage', 'constraintLongOnly', 'constraintNoHighFreq', 'constraintStopLoss', 'constraintExplainable', 'constraintLowTurnover'] as const
const constraintList = computed(() => constraintKeys.map((key) => ({ key, label: t(`aiLab.${key}`) })))

const quickRefineHintKeys = ['refineLowerDrawdown', 'refineAddStopLoss', 'refineReduceFreq', 'refineDailyTf', 'refineTightenBounds'] as const
const quickRefineHints = computed(() => quickRefineHintKeys.map((key) => ({ key, label: t(`aiLab.${key}`) })))

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
  constraints: ['constraintNoLeverage', 'constraintStopLoss', 'constraintExplainable'],
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

const sessions = ref<AiSessionSummary[]>([])
const activeSessionId = ref<string | null>(null)
const historyLoaded = ref(false)
const historyOpen = ref(true)

const briefQuality = computed(() => {
  let score = 0
  if (brief.symbol && brief.market && brief.timeframe) score += 1
  if (brief.strategyStyle && brief.direction && brief.constraints.length >= 2) score += 1
  if (brief.notes || brief.riskLimits.maxDrawdownPct || brief.riskLimits.positionRatio) score += 1
  const labels = [t('aiLab.briefQualityIncomplete'), t('aiLab.briefQualityEnough'), t('aiLab.briefQualityStrong')]
  return { score, label: labels[Math.max(0, score - 1)] ?? labels[0] }
})

const currentStage = computed<GenerationStage>(() => {
  if (aiSubmitting.value) return 'design'
  if (!aiLatestAnalysis.value && aiMessages.value.length > 0) return 'clarify'
  if (!aiLatestAnalysis.value) return 'brief'
  if (validationState.value === 'block') return 'validate'
  return 'package'
})

const currentStageLabel = computed(() => stages.value.find((stage) => stage.key === currentStage.value)?.label ?? 'AI')

const hasEntrypoint = computed(() => (aiLatestAnalysis.value?.entrypointCandidates.length ?? 0) > 0)

const qsgaStatus = computed(() => aiLatestAnalysis.value?.qsgaStatus || '')

const qsgaStatusLabel = computed(() => {
  const labels: Record<string, string> = {
    draft_ready: copy.value.qsgaDraftReady,
    running: copy.value.qsgaRunning,
    clarification_required: copy.value.qsgaClarification,
    rejected: copy.value.qsgaRejected,
    blocked: copy.value.qsgaBlocked,
  }
  return labels[qsgaStatus.value] || qsgaStatus.value
})

const trustedQsgaRequiredChecks = ['guardrails', 'schema', 'domain', 'semantic', 'qysp', 'runtime', 'backtest', 'risk']

const qsgaTrust = computed(() => aiLatestAnalysis.value?.qsgaTrust || null)

const qsgaTrustBlockingChecks = computed(() => {
  const trust = qsgaTrust.value
  if (Array.isArray(trust?.blockingChecks)) return trust.blockingChecks
  const verification = aiLatestAnalysis.value?.verification
  if (!qsgaStatus.value || !verification || typeof verification !== 'object') return []
  return trustedQsgaRequiredChecks.filter((check) => String(verification[check]?.status || 'not_run') !== 'pass')
})

const qsgaTrustPassed = computed(() => {
  if (!qsgaStatus.value) return true
  if (typeof qsgaTrust.value?.trusted === 'boolean') return qsgaTrust.value.trusted
  return qsgaTrustBlockingChecks.value.length === 0
})

const qsgaTrustNotice = computed(() => {
  if (!qsgaStatus.value) return ''
  if (qsgaTrustPassed.value) return copy.value.qsgaTrusted
  const blocking = qsgaTrustBlockingChecks.value
  const failed = Array.isArray(qsgaTrust.value?.failedChecks) ? qsgaTrust.value.failedChecks : []
  if (
    ['draft_ready', 'running'].includes(qsgaStatus.value)
    && blocking.some((check) => ['backtest', 'risk'].includes(check))
  ) {
    return copy.value.qsgaTrustPending
  }
  return copy.value.qsgaTrustBlocked.replace('{checks}', (failed.length ? failed : blocking).join(', ') || '-')
})

const qsgaVerificationEntries = computed(() => {
  const verification = aiLatestAnalysis.value?.verification
  if (!verification || typeof verification !== 'object') return []
  return Object.entries(verification).map(([key, result]) => ({
    key,
    label: key,
    status: String(result?.status || 'not_run'),
  }))
})

const qsgaMessages = computed(() => {
  const verification = aiLatestAnalysis.value?.verification
  if (!verification || typeof verification !== 'object') return []
  const messages: string[] = []
  Object.values(verification).forEach((result) => {
    ;(result?.errors || []).forEach((error) => {
      if (error.message || error.code) messages.push(String(error.message || error.code))
    })
    ;(result?.questions || []).forEach((question) => {
      if (question.message) messages.push(String(question.message))
    })
  })
  return messages
})

const qyirPreview = computed(() => {
  const qyir = aiLatestAnalysis.value?.qyir
  return qyir ? JSON.stringify(qyir, null, 2) : ''
})

const validationState = computed<ValidationState>(() => {
  const analysis = aiLatestAnalysis.value
  if (!analysis) return 'warn'
  if (qsgaStatus.value && qsgaStatus.value !== 'draft_ready') return 'block'
  if (qsgaStatus.value && !qsgaTrustPassed.value) return 'block'
  if (!hasEntrypoint.value || analysis.errors.length > 0) return 'block'
  if (analysis.warnings.length > 0) return 'warn'
  return 'pass'
})

const aiCanAdopt = computed(() => {
  const analysis = aiLatestAnalysis.value
  if (!analysis?.draftImportId || validationState.value === 'block') return false
  return !qsgaStatus.value || (qsgaStatus.value === 'draft_ready' && qsgaTrustPassed.value)
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

const stageOrder: GenerationStage[] = ['brief', 'clarify', 'design', 'validate', 'package']

function stageDone(idx: number): boolean {
  const currentIdx = stageOrder.indexOf(currentStage.value)
  return idx < currentIdx
}

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

const constraintLabelMap: Record<string, Record<string, string>> = {
  en: {
    constraintNoLeverage: 'No leverage',
    constraintLongOnly: 'Long only',
    constraintNoHighFreq: 'No high frequency',
    constraintStopLoss: 'Stop loss required',
    constraintExplainable: 'Explainable rules',
    constraintLowTurnover: 'Low turnover',
  },
  zh: {
    constraintNoLeverage: '禁止杠杆',
    constraintLongOnly: '仅做多',
    constraintNoHighFreq: '禁止高频',
    constraintStopLoss: '必须止损',
    constraintExplainable: '规则可解释',
    constraintLowTurnover: '低换手率',
  },
}

function compileBriefMessage(): string {
  const lang = isZh.value ? 'zh' : 'en'
  const labels = constraintLabelMap[lang]
  const constraintText = brief.constraints.map((key) => labels[key] || key).join(', ') || (lang === 'zh' ? '无' : 'none')

  if (lang === 'zh') {
    const lines = [
      '请根据以下结构化需求，生成一份可在 QYQuant 平台运行的策略草案。',
      `模式: ${brief.mode}`,
      `市场: ${brief.market}`,
      `标的: ${brief.symbol}`,
      `周期: ${brief.timeframe}`,
      `风格: ${brief.strategyStyle}`,
      `方向: ${brief.direction}`,
      `风险: 最大回撤 ${brief.riskLimits.maxDrawdownPct}%，仓位比例 ${brief.riskLimits.positionRatio}%`,
      `约束: ${constraintText}`,
    ]
    if (brief.notes) lines.push(`用户备注: ${brief.notes}`)
    if (aiPrompt.value) lines.push(`补充要求: ${aiPrompt.value}`)
    lines.push('请返回策略代码、元数据、参数定义、假设说明以及验证警告（如有）。')
    return lines.join('\n')
  }

  const lines = [
    'Create a QYQuant executable strategy draft from this structured brief.',
    `Mode: ${brief.mode}`,
    `Market: ${brief.market}`,
    `Symbol: ${brief.symbol}`,
    `Timeframe: ${brief.timeframe}`,
    `Style: ${brief.strategyStyle}`,
    `Direction: ${brief.direction}`,
    `Risk: max drawdown ${brief.riskLimits.maxDrawdownPct}%, position ratio ${brief.riskLimits.positionRatio}%`,
    `Constraints: ${constraintText}`,
  ]
  if (brief.notes) lines.push(`User notes: ${brief.notes}`)
  if (aiPrompt.value) lines.push(`Additional request: ${aiPrompt.value}`)
  lines.push('Return strategy code, metadata, parameter definitions, assumptions, and validation warnings if any.')
  return lines.join('\n')
}

function qsgaBriefSnapshot() {
  return {
    mode: brief.mode,
    market: brief.market,
    symbol: brief.symbol,
    timeframe: brief.timeframe,
    strategyStyle: brief.strategyStyle,
    direction: brief.direction,
    riskLimits: { ...brief.riskLimits },
    constraints: [...brief.constraints],
    notes: brief.notes,
  }
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
      locale: isZh.value ? 'zh' : 'en',
      sessionId: activeSessionId.value || undefined,
      mode: 'qsga',
      options: {
        qsgaBrief: qsgaBriefSnapshot(),
        runBacktest: true,
      },
    })
    aiMessages.value = [...pendingMessages, { role: 'assistant', content: result.reply }]
    aiLatestAnalysis.value = result.analysis
    activeSessionId.value = result.sessionId
    activeMobileTab.value = result.analysis ? 'draft' : 'console'
    void loadSessionList()
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
    low: t('aiLab.riskLevelLow'),
    medium: t('aiLab.riskLevelMedium'),
    high: t('aiLab.riskLevelHigh'),
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

function verificationStatusClass(status: string) {
  if (status === 'pass') return 'validation-state validation-state--pass'
  if (status === 'not_run') return 'validation-state validation-state--muted'
  return 'validation-state validation-state--warn'
}

async function loadSessionList() {
  try {
    const response = await listAiSessions({ perPage: 50 })
    sessions.value = response.data ?? []
    historyLoaded.value = true
  } catch {
    // silent — history is supplementary
  }
}

async function loadSession(sessionId: string) {
  try {
    const detail = await getAiSession(sessionId)
    activeSessionId.value = detail.id
    aiMessages.value = detail.messages || []
    aiLatestAnalysis.value = detail.analysis
    activeMobileTab.value = detail.analysis ? 'draft' : 'console'
  } catch {
    aiError.value = t('aiLab.loadError')
  }
}

function startNewSession() {
  activeSessionId.value = null
  aiMessages.value = []
  aiLatestAnalysis.value = null
  aiError.value = ''
  activeMobileTab.value = 'console'
}

async function handleDeleteSession(sessionId: string) {
  if (!confirm(t('aiLab.deleteConfirm'))) return
  try {
    await deleteAiSession(sessionId)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (activeSessionId.value === sessionId) {
      startNewSession()
    }
  } catch {
    aiError.value = t('aiLab.deleteError')
  }
}

onMounted(() => {
  void loadAiIntegrations()
  void loadSessionList()
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════
   AI Strategy Lab — Premium Quant Terminal
   ═══════════════════════════════════════════════════════ */

.ai-lab-view {
  width: 100%;
  position: relative;
  animation: labFadeIn 600ms var(--ease-out-expo) both;
}

@keyframes labFadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* ── Ambient Background ── */
.ai-lab-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.ai-lab-ambient__grid {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle, rgba(25, 118, 210, 0.06) 1px, transparent 1px);
  background-size: 32px 32px;
}

.ai-lab-ambient__glow {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.12;
}

.ai-lab-ambient__glow--left {
  top: 10%;
  left: -10%;
  background: var(--color-accent);
}

.ai-lab-ambient__glow--right {
  bottom: 5%;
  right: -8%;
  background: var(--color-primary);
}

.ai-lab-shell {
  position: relative;
  z-index: 1;
  margin: 0 auto;
  padding: 0 var(--spacing-lg) var(--spacing-xl);
}

/* ── Layout Primitives ── */
.ai-lab-header,
.panel-heading--row,
.ai-lab-header__actions,
.ai-lab-eyebrow-row,
.stage-rail__track,
.mobile-tabs,
.console-actions,
.draft-actions {
  display: flex;
  align-items: center;
}

.ai-lab-header__copy,
.panel-heading,
.research-log__empty,
.draft-placeholder,
.empty-state {
  display: grid;
  gap: var(--spacing-xs);
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

/* ── Header ── */
.ai-lab-header {
  justify-content: space-between;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl) 0 var(--spacing-lg);
}

.ai-lab-eyebrow-row {
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.ai-lab-header__divider {
  width: 1px;
  height: 16px;
  background: var(--color-border-light);
}

.ai-lab-header h1 {
  margin: 0;
  font-size: clamp(24px, 3.2vw, 38px);
  line-height: 1.05;
  letter-spacing: -0.04em;
  font-weight: 900;
  color: var(--color-text-primary);
}

.ai-lab-header p {
  color: var(--color-text-muted);
  font-size: var(--font-size-md);
  line-height: 1.6;
  max-width: 520px;
}

.ai-lab-eyebrow {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.ai-lab-header__actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* ── Connection Pill ── */
.connection-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 4px 12px;
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  transition: all var(--transition-normal);
}

.connection-pill--ready {
  border-color: rgba(46, 125, 50, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-text-muted);
  transition: background var(--transition-normal);
}

.connection-pill--ready .status-dot {
  background: var(--color-success);
  box-shadow: 0 0 8px rgba(46, 125, 50, 0.5);
}

.connection-pill--loading .status-dot {
  animation: statusPulse 1.5s ease-in-out infinite;
}

.connection-pill--blocked .status-dot,
.draft-status--block .status-dot {
  background: var(--color-danger);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.3; }
}

/* ── Stage Rail ── */
.stage-rail {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-sm) 0;
  overflow-x: auto;
}

.stage-rail__track {
  gap: 0;
  width: 100%;
  min-width: max-content;
}

.stage-rail__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  transition: color var(--transition-normal);
}

.stage-rail__dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--color-border-light);
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-normal);
}

.stage-rail__dot-inner {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-light);
  transition: all var(--transition-normal);
}

.stage-rail__line {
  flex: 1;
  min-width: 24px;
  height: 2px;
  background: var(--color-border-light);
  margin: 0 var(--spacing-xs);
  transition: background var(--transition-normal);
}

.stage-rail__item--done .stage-rail__dot {
  border-color: var(--color-primary);
  background: var(--color-primary);
}

.stage-rail__item--done .stage-rail__dot-inner {
  background: #fff;
}

.stage-rail__item--done .stage-rail__line {
  background: var(--color-primary);
}

.stage-rail__item--done {
  color: var(--color-primary);
}

.stage-rail__item--active .stage-rail__dot {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: 0 0 0 4px rgba(25, 118, 210, 0.12), 0 0 16px rgba(25, 118, 210, 0.15);
}

.stage-rail__item--active .stage-rail__dot-inner {
  background: var(--color-primary);
  box-shadow: 0 0 6px rgba(25, 118, 210, 0.5);
}

.stage-rail__item--active {
  color: var(--color-primary);
}

.stage-rail__item--active .stage-rail__label {
  font-weight: 800;
}

/* ── Three-Panel Grid ── */
.ai-lab-grid {
  display: grid;
  grid-template-columns: 1fr 1.6fr 1fr;
  gap: var(--spacing-md);
  align-items: stretch;
}

.ai-lab-grid--history-open {
  grid-template-columns: 220px 1fr 1.6fr 1fr;
}

.ai-lab-grid > .brief-panel  { animation: panelReveal 500ms var(--ease-out-expo) 80ms both; }
.ai-lab-grid > .console-panel { animation: panelReveal 500ms var(--ease-out-expo) 160ms both; }
.ai-lab-grid > .draft-panel  { animation: panelReveal 500ms var(--ease-out-expo) 240ms both; }

@keyframes panelReveal {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Panel Base ── */
.lab-panel {
  min-width: 0;
  padding: var(--spacing-lg);
  border: 1.5px solid var(--color-border-light);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.03);
  display: grid;
  gap: var(--spacing-md);
  align-content: start;
  transition: box-shadow var(--transition-slow), border-color var(--transition-slow);
}

.lab-panel:hover {
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 8px 24px rgba(0, 0, 0, 0.06);
}

/* ── Brief Panel (left) ── */
.brief-panel {
  position: relative;
  overflow: hidden;
}

.brief-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-accent), #fdd835);
}

/* ── Console Panel (center) ── */
.console-panel {
  position: relative;
  overflow: hidden;
}

.console-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary), #42a5f5);
}

/* ── Draft Panel (right) ── */
.draft-panel {
  position: relative;
  overflow: hidden;
}

.draft-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #43a047, #66bb6a);
}

/* ── Panel Headings ── */
.panel-heading {
  padding-bottom: var(--spacing-sm);
  border-bottom: 1.5px solid var(--color-border-light);
}

.panel-heading h2 {
  font-weight: 700;
  font-size: var(--font-size-lg);
  letter-spacing: -0.01em;
}

.panel-kicker {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.7;
}

.brief-panel .panel-kicker { color: var(--color-accent); }
.draft-panel .panel-kicker { color: #43a047; }

.panel-heading--row {
  justify-content: space-between;
  gap: var(--spacing-md);
}

/* ── Mode Switch ── */
.mode-switch {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.mode-option {
  min-width: 0;
  padding: 10px 8px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-option:hover {
  border-color: var(--color-border);
  background: var(--color-surface-hover);
}

.mode-option strong,
.mode-option span {
  display: block;
}

.mode-option strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.mode-option span {
  margin-top: 2px;
  font-size: 10px;
  line-height: 1.3;
  color: var(--color-text-muted);
}

.mode-option--active {
  border-color: var(--color-accent);
  background: var(--color-accent-bg);
  box-shadow: 0 0 0 3px rgba(249, 168, 37, 0.08);
}

/* ── Brief Quality ── */
.brief-quality {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
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
  gap: 3px;
}

.brief-quality__meter span {
  height: 4px;
  border-radius: 2px;
  background: var(--color-border-light);
  transition: all var(--transition-normal);
}

.brief-quality__meter .brief-quality__bar--active {
  background: linear-gradient(90deg, var(--color-accent), #fdd835);
  box-shadow: 0 0 6px rgba(249, 168, 37, 0.25);
}

/* ── Fields ── */
.field,
.prompt-box {
  display: grid;
  gap: 4px;
}

.field > span,
.prompt-box > span {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.field-control,
.prompt-box textarea {
  width: 100%;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-md);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.field-control {
  min-height: 36px;
  padding: 7px 10px;
}

.field-control:focus,
.prompt-box textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.08);
  outline: none;
}

.field-control--textarea,
.prompt-box textarea {
  min-height: 100px;
  padding: 10px;
  resize: vertical;
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-xs);
}

/* ── Chips & Controls ── */
.segmented-control,
.constraint-list,
.quick-refine {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.segmented-control button,
.constraint-chip,
.quick-refine__chip,
.mobile-tab {
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-xs);
  font-weight: 700;
  transition: all var(--transition-fast);
}

.segmented-control button {
  flex: 1;
  min-height: 32px;
}

.constraint-chip,
.quick-refine__chip {
  padding: 5px 10px;
}

.constraint-chip:hover,
.quick-refine__chip:hover {
  border-color: var(--color-border);
  transform: translateY(-1px);
}

.segmented-control button.active,
.constraint-chip--active,
.mobile-tab--active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.constraint-chip--active {
  border-color: var(--color-accent);
  background: var(--color-accent);
  color: var(--color-text-primary);
  box-shadow: 0 2px 8px rgba(249, 168, 37, 0.15);
}

.quick-refine__chip:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

/* ── Empty States ── */
.empty-state {
  min-height: 380px;
  place-items: center;
  text-align: center;
  border: 2px dashed var(--color-border-light);
  border-radius: 12px;
  background: var(--color-surface);
}

.empty-state p,
.draft-placeholder p,
.research-log__empty p {
  color: var(--color-text-primary);
  font-weight: 700;
}

.empty-state--blocked {
  padding: var(--spacing-xl);
}

.connection-select {
  max-width: 360px;
}

/* ── Research Log ── */
.research-log {
  min-height: 300px;
  max-height: 460px;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 1.5px solid var(--color-border-light);
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(25, 118, 210, 0.02), transparent 40%),
    var(--color-surface);
  position: relative;
}

.research-log::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 32px;
  background: linear-gradient(transparent, var(--color-surface));
  pointer-events: none;
  border-radius: 0 0 10px 10px;
}

.research-log__empty {
  min-height: 260px;
  place-items: center;
  text-align: center;
}

.research-entry {
  display: grid;
  gap: 6px;
  padding: 10px 14px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
  transition: all var(--transition-fast);
}

.research-entry:hover {
  border-color: var(--color-border);
}

.research-entry--assistant {
  border-left: 3px solid var(--color-primary);
  background:
    linear-gradient(90deg, rgba(25, 118, 210, 0.03), var(--color-surface) 50%);
}

.research-entry--user {
  border-left: 3px solid var(--color-accent);
  background:
    linear-gradient(90deg, rgba(249, 168, 37, 0.03), var(--color-surface) 50%);
}

.research-entry__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.research-entry p {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.65;
  font-size: var(--font-size-md);
}

.prompt-box textarea {
  min-height: 100px;
}

/* ── Actions ── */
.console-actions,
.draft-actions {
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: var(--radius-full);
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-top-color: var(--color-primary);
  animation: spin 0.7s linear infinite;
}

.form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.error {
  color: var(--color-danger);
}

/* ── Draft Panel Content ── */
.draft-placeholder {
  min-height: 400px;
  place-items: center;
  text-align: center;
  border: 2px dashed var(--color-border-light);
  border-radius: 12px;
  background: var(--color-surface);
}

.draft-status {
  padding: 10px 14px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
  transition: all var(--transition-normal);
}

.draft-status--pass {
  border-color: rgba(46, 125, 50, 0.3);
  background: var(--color-success-bg);
}

.draft-status--pass .status-dot {
  background: var(--color-success);
  box-shadow: 0 0 8px rgba(46, 125, 50, 0.4);
}

.draft-status--warn {
  border-color: rgba(230, 81, 0, 0.3);
  background: var(--color-warning-bg);
}

.draft-status--block {
  border-color: rgba(212, 57, 59, 0.3);
  background: var(--color-danger-bg);
}

.summary-card,
.draft-section {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
  transition: border-color var(--transition-fast);
}

.summary-card:hover,
.draft-section:hover {
  border-color: var(--color-border);
}

.summary-card strong,
.parameter-table strong,
.validation-item strong {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}

.draft-section h3 {
  color: var(--color-text-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.draft-section p,
.muted-copy {
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-size: var(--font-size-md);
}

.parameter-table {
  display: grid;
  gap: 2px;
}

.parameter-table__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-sm);
  padding: 8px 0;
  border-top: 1px solid var(--color-border-light);
  transition: background var(--transition-fast);
}

.parameter-table__row:hover {
  background: rgba(25, 118, 210, 0.02);
}

.parameter-table__row--head {
  border-top: none;
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.validation-list {
  display: grid;
  gap: 6px;
}

.validation-state--pass {
  color: var(--color-success);
}

.validation-state--warn {
  color: var(--color-warning);
}

.validation-state--muted {
  color: var(--color-text-muted);
}

.qsga-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: 8px 12px;
  border: 1.5px solid var(--color-border-light);
  border-radius: 8px;
  background: var(--color-surface);
}

.qsga-status span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.qsga-status strong {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}

.qyir-preview {
  max-height: 260px;
  margin: 0;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
}

.summary-alert {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: var(--font-size-sm);
  line-height: 1.5;
  border-width: 1.5px;
  border-style: solid;
}

.summary-alert--warning {
  border-color: rgba(230, 81, 0, 0.25);
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.summary-alert--success {
  border-color: rgba(46, 125, 50, 0.25);
  background: var(--color-success-bg);
  color: var(--color-success);
}

.summary-alert--error {
  border-color: rgba(212, 57, 59, 0.25);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

/* ── History Panel ── */
.history-panel {
  overflow: hidden;
}

.history-panel::before {
  background: linear-gradient(90deg, #7e57c2, #9575cd) !important;
}

.history-new-btn {
  width: 100%;
  padding: 8px;
  border: 1.5px dashed var(--color-primary);
  border-radius: 8px;
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font: inherit;
  font-size: var(--font-size-xs);
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.history-new-btn:hover {
  background: var(--color-primary);
  color: #fff;
}

.history-loading,
.history-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  padding: var(--spacing-lg) 0;
}

.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 4px;
  overflow-y: auto;
  max-height: 500px;
}

.history-item {
  display: flex;
  align-items: center;
  border: 1.5px solid transparent;
  border-radius: 8px;
  transition: all var(--transition-fast);
}

.history-item:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-light);
}

.history-item--active {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.history-item__body {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font: inherit;
  display: grid;
  gap: 2px;
}

.history-item__title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.history-item__meta {
  font-size: 10px;
  color: var(--color-text-muted);
}

.history-item__delete {
  padding: 4px 8px;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: var(--font-size-lg);
  line-height: 1;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.history-item:hover .history-item__delete {
  opacity: 1;
}

.history-item__delete:hover {
  color: var(--color-danger);
}

.btn-sm {
  padding: 2px 8px;
  font-size: var(--font-size-lg);
  line-height: 1;
}

/* ── Mobile Tabs ── */
.mobile-tabs {
  display: none;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.mobile-tab {
  flex: 1;
  min-height: 36px;
}

/* ── Keyframes ── */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Responsive ── */
@media (max-width: 1180px) {
  .ai-lab-grid,
  .ai-lab-grid--history-open {
    grid-template-columns: 1fr;
  }

  .history-panel {
    display: none;
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

  .ai-lab-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .ai-lab-header__actions,
  .panel-heading--row {
    align-items: stretch;
    flex-direction: column;
  }

  .ai-lab-header h1 {
    font-size: clamp(22px, 6vw, 30px);
  }

  .mode-switch,
  .risk-grid {
    grid-template-columns: 1fr;
  }

  .ai-lab-ambient__grid {
    background-size: 24px 24px;
  }
}
</style>
