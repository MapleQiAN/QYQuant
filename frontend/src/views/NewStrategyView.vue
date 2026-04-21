<template>
  <section class="new-strategy-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">{{ $t('pageTitle.strategies') }}</p>
          <h1 class="page-title">{{ $t('strategyNew.title') }}</h1>
          <p class="page-subtitle">{{ $t('strategyNew.subtitle') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/">
          <ArrowLeftIcon />
          {{ $t('strategyNew.back') }}
        </RouterLink>
      </div>

      <div class="path-grid">
        <!-- Row 1: AI card — full width -->
        <article class="card path-card path-card--ai" @click="openAiBuilder">
          <div class="path-card--ai__glow"></div>
          <div class="path-card--ai__content">
            <div class="path-card__header">
              <div class="path-card--ai__badge-row">
                <span class="path-badge path-badge--accent">{{ $t('strategyNew.aiBadge') }}</span>
                <span class="path-card--ai__spark">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z" fill="currentColor"/></svg>
                </span>
              </div>
              <h2>{{ $t('strategyNew.aiTitle') }}</h2>
              <p class="path-card__description">{{ $t('strategyNew.aiDescription') }}</p>
              <div class="ai-highlight-tags">
                <span class="ai-tag">{{ $t('strategyNew.aiTagQyir') }}</span>
                <span class="ai-tag">{{ $t('strategyNew.aiTagNonTuring') }}</span>
                <span class="ai-tag">{{ $t('strategyNew.aiTagVerifiable') }}</span>
                <span class="ai-tag">{{ $t('strategyNew.aiTagAuditable') }}</span>
              </div>
            </div>
            <div class="path-card__body">
              <div class="path-checklist">
                <span class="path-check">{{ $t('strategyNew.aiChecklist.one') }}</span>
                <span class="path-check">{{ $t('strategyNew.aiChecklist.two') }}</span>
                <span class="path-check">{{ $t('strategyNew.aiChecklist.three') }}</span>
                <span class="path-check">{{ $t('strategyNew.aiChecklist.four') }}</span>
                <span class="path-check">{{ $t('strategyNew.aiChecklist.five') }}</span>
              </div>
              <RouterLink class="ai-learn-more" :to="{ name: 'ai-trust' }" @click.stop>
                {{ $t('strategyNew.aiLearnMore') }}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </RouterLink>
            </div>
          </div>
          <div class="path-card--ai__action">
            <button
              data-test="open-ai-builder"
              class="btn btn-primary"
              type="button"
              @click.stop="openAiBuilder"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z"/></svg>
              {{ $t('strategyNew.aiAction') }}
            </button>
          </div>
        </article>

        <!-- Row 2: Template + Import — two columns -->
        <article class="card path-card">
          <div class="path-card__header">
            <span class="path-badge">{{ $t('strategyNew.recommendedBadge') }}</span>
            <h2>{{ $t('strategyNew.templateTitle') }}</h2>
            <p>{{ $t('strategyNew.templateHint') }}</p>
          </div>
          <div class="path-card__body">
            <div class="path-checklist">
              <span class="path-check">{{ $t('strategyNew.templateChecklist.one') }}</span>
              <span class="path-check">{{ $t('strategyNew.templateChecklist.two') }}</span>
              <span class="path-check">{{ $t('strategyNew.templateChecklist.three') }}</span>
            </div>
            <button
              data-test="open-template-picker"
              class="btn btn-primary"
              type="button"
              :disabled="templateState.loading"
              @click="templatePickerOpen = true"
            >
              <span v-if="templateState.loading" class="btn-spinner"></span>
              {{ $t('strategyNew.templateAction') }}
            </button>
            <p v-if="templateState.error" class="form-message error">{{ templateState.error }}</p>
          </div>
        </article>

        <article class="card path-card">
          <div class="path-card__header">
            <h2>{{ $t('strategyNew.importTitle') }}</h2>
            <p>{{ $t('strategyNew.importHint') }}</p>
          </div>
          <div class="path-card__body">
            <div class="import-visual">
              <div class="import-visual__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              </div>
              <p class="import-visual__text">{{ $t('strategyNew.importNote') }}</p>
            </div>
            <div class="tag-row">
              <span class="pill">.py</span>
              <span class="pill">.zip</span>
              <span class="pill pill--accent">.qys</span>
            </div>
            <div class="path-checklist">
              <span class="path-check">{{ $t('strategyNew.importChecklist.one') }}</span>
              <span class="path-check">{{ $t('strategyNew.importChecklist.two') }}</span>
              <span class="path-check">{{ $t('strategyNew.importChecklist.three') }}</span>
            </div>
            <RouterLink class="btn btn-primary" to="/strategies/import">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              {{ $t('strategyNew.importAction') }}
            </RouterLink>
          </div>
        </article>
      </div>

      <section class="card guide-card">
        <button data-test="guide-toggle" class="guide-toggle" type="button" @click="isGuideOpen = !isGuideOpen">
          <div class="guide-toggle__copy">
            <p class="guide-eyebrow">{{ $t('strategyNew.guideTitle') }}</p>
            <h2>{{ $t('strategyNew.guideIntro') }}</h2>
            <p class="guide-toggle__hint">{{ $t('strategyNew.guideHint') }}</p>
          </div>
          <span class="guide-toggle__icon" :class="{ 'guide-toggle__icon--open': isGuideOpen }">⌄</span>
        </button>

        <div v-if="isGuideOpen" class="guide-content">
          <div class="guide-grid">
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideExecutionTitle') }}</h3>
              <p>{{ $t('strategyNew.guideExecutionBody') }}</p>
              <ol class="guide-list guide-list--ordered">
                <li>{{ $t('strategyNew.guideStep1') }}</li>
                <li>{{ $t('strategyNew.guideStep2') }}</li>
                <li>{{ $t('strategyNew.guideStep3') }}</li>
              </ol>
            </div>
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideExampleTitle') }}</h3>
              <pre class="guide-code"><code>{{ minimalGuideCode }}</code></pre>
            </div>
          </div>

          <div class="guide-grid">
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideApiTitle') }}</h3>
              <ul class="guide-list">
                <li>{{ $t('strategyNew.guideApiCtx') }}</li>
                <li>{{ $t('strategyNew.guideApiData') }}</li>
                <li>{{ $t('strategyNew.guideApiOrder') }}</li>
              </ul>
            </div>
            <div class="guide-section">
              <h3>{{ $t('strategyNew.guideErrorsTitle') }}</h3>
              <ul class="guide-list">
                <li>{{ $t('strategyNew.guideErrorEntrypoint') }}</li>
                <li>{{ $t('strategyNew.guideErrorSyntax') }}</li>
                <li>{{ $t('strategyNew.guideErrorReturn') }}</li>
              </ul>
            </div>
          </div>

          <div class="guide-actions">
            <RouterLink
              class="btn btn-primary"
              :to="{ name: 'strategy-writing-guide' }"
              data-testid="strategy-guide-primary"
            >
              {{ $t('strategyNew.guidePrimaryAction') }}
            </RouterLink>
            <RouterLink
              class="btn btn-secondary"
              :to="{ name: 'strategy-writing-guide', hash: '#spec-reference' }"
              data-testid="strategy-guide-secondary"
            >
              {{ $t('strategyNew.guideSecondaryAction') }}
            </RouterLink>
          </div>
        </div>
      </section>

      <div v-if="templatePickerOpen" class="overlay-backdrop" @click.self="templatePickerOpen = false">
        <div class="card template-picker">
          <div class="template-picker__header">
            <div>
              <p class="guide-eyebrow">{{ $t('strategyNew.templatePickerTitle') }}</p>
              <h2>{{ $t('strategyNew.templatePickerSubtitle') }}</h2>
            </div>
            <button class="btn btn-secondary" type="button" @click="templatePickerOpen = false">
              {{ $t('common.close') }}
            </button>
          </div>

          <div class="template-grid">
            <button
              v-for="template in templates"
              :key="template.id"
              :data-test="`template-card-${template.id}`"
              class="template-card"
              type="button"
              @click="handleTemplateSelect(template)"
            >
              <h3>{{ $t(template.nameKey) }}</h3>
              <p>{{ $t(template.descriptionKey) }}</p>
            </button>
          </div>
        </div>
      </div>

      <div v-if="aiModalOpen" class="overlay-backdrop" @click.self="aiModalOpen = false">
        <div class="card ai-builder">
          <div class="template-picker__header">
            <div>
              <p class="guide-eyebrow">{{ $t('strategyNew.aiTitle') }}</p>
              <h2>{{ $t('strategyNew.aiModalTitle') }}</h2>
              <p class="page-subtitle">{{ $t('strategyNew.aiModalHint') }}</p>
            </div>
            <button class="btn btn-secondary" type="button" @click="aiModalOpen = false">
              {{ $t('common.close') }}
            </button>
          </div>

          <div v-if="aiLoadingIntegrations" class="empty-panel">
            {{ $t('strategyNew.aiLoading') }}
          </div>

          <div v-else class="ai-builder__grid">
            <section class="ai-sidepanel">
              <div class="card ai-panel">
                <h3>{{ $t('strategyNew.aiConnectionTitle') }}</h3>

                <template v-if="aiIntegrations.length > 0">
                  <label class="field">
                    <span class="field-label">{{ $t('strategyNew.aiIntegrationLabel') }}</span>
                    <QSelect v-model="selectedAiIntegrationId" :options="aiIntegrationOptions" data-test="ai-integration-select" />
                  </label>
                  <p class="field-hint">{{ $t('strategyNew.aiReuseHint') }}</p>
                </template>

                <template v-else>
                  <p class="field-hint">{{ $t('strategyNew.aiSetupHint') }}</p>
                  <button
                    data-test="ai-open-settings"
                    class="btn btn-primary"
                    type="button"
                    @click="openAiSettings"
                  >
                    {{ $t('strategyNew.aiOpenSettingsAction') }}
                  </button>
                </template>
              </div>

              <div v-if="aiLatestAnalysis" class="card ai-panel">
                <h3>{{ $t('strategyNew.aiDraftTitle') }}</h3>
                <div class="summary-rows">
                  <div class="summary-row">
                    <span class="summary-label">{{ $t('strategyNew.nameLabel') }}</span>
                    <span class="summary-value">{{ String(aiLatestMetadata.name || '-') }}</span>
                  </div>
                  <div class="summary-row">
                    <span class="summary-label">{{ $t('strategyNew.symbolLabel') }}</span>
                    <span class="summary-value">{{ String(aiLatestMetadata.symbol || '-') }}</span>
                  </div>
                  <div class="summary-row">
                    <span class="summary-label">{{ $t('marketplace.category') }}</span>
                    <span class="summary-value">{{ formatCategory(String(aiLatestMetadata.category || '-')) }}</span>
                  </div>
                  <div v-if="aiLatestMetadata.timeframe" class="summary-row">
                    <span class="summary-label">{{ $t('strategyPreview.timeframe') }}</span>
                    <span class="summary-value">{{ String(aiLatestMetadata.timeframe) }}</span>
                  </div>
                  <div v-if="aiLatestMetadata.riskLevel" class="summary-row">
                    <span class="summary-label">{{ $t('strategyPreview.riskLevel') }}</span>
                    <span class="summary-value" :class="`risk-badge risk-badge--${aiLatestMetadata.riskLevel}`">{{ riskLevelLabel(String(aiLatestMetadata.riskLevel)) }}</span>
                  </div>
                </div>

                <div v-if="aiLatestMetadata.logicExplanation" class="draft-section">
                  <h4 class="draft-section__title">{{ $t('strategyPreview.logicTitle') }}</h4>
                  <p class="draft-section__text">{{ String(aiLatestMetadata.logicExplanation) }}</p>
                </div>

                <div v-if="aiLatestMetadata.riskRules" class="draft-section">
                  <h4 class="draft-section__title">{{ $t('strategyPreview.riskRulesTitle') }}</h4>
                  <p class="draft-section__text">{{ String(aiLatestMetadata.riskRules) }}</p>
                </div>

                <div v-if="aiLatestMetadata.suitableMarket" class="draft-section">
                  <h4 class="draft-section__title">{{ $t('strategyPreview.suitableMarket') }}</h4>
                  <p class="draft-section__text">{{ String(aiLatestMetadata.suitableMarket) }}</p>
                </div>

                <div v-if="aiLatestAnalysis.parameterCandidates.length" class="draft-section">
                  <h4 class="draft-section__title">{{ $t('strategyNew.aiParamsDetected') }}</h4>
                  <div class="param-chips">
                    <span v-for="param in aiLatestAnalysis.parameterCandidates" :key="param.key" class="param-chip">
                      {{ param.user_facing && 'label' in param.user_facing ? param.user_facing.label : param.key }}: {{ param.default }}
                    </span>
                  </div>
                </div>

                <div class="validation-block">
                  <h4 class="validation-title">{{ $t('strategyNew.aiValidationTitle') }}</h4>
                  <div class="validation-list">
                    <div class="validation-item">
                      <span>{{ $t('strategy.import.validationEntrypoint') }}</span>
                      <strong :class="validationClass(aiLatestAnalysis.entrypointCandidates.length > 0)">{{ validationLabel(aiLatestAnalysis.entrypointCandidates.length > 0) }}</strong>
                    </div>
                    <div v-if="aiLatestAnalysis.parameterCandidates.length" class="validation-item">
                      <span>{{ $t('strategyNew.aiParamsDetected') }}</span>
                      <strong class="validation-state validation-state--pass">{{ aiLatestAnalysis.parameterCandidates.length }}</strong>
                    </div>
                  </div>
                </div>

                <div v-if="aiLatestAnalysis.warnings.length" class="summary-alert summary-alert--warning">
                  {{ aiLatestAnalysis.warnings.join(', ') }}
                </div>
                <div v-if="aiLatestAnalysis.errors.length" class="summary-alert summary-alert--error">
                  {{ aiLatestAnalysis.errors.join(', ') }}
                </div>
                <button
                  data-test="ai-adopt"
                  class="btn btn-primary btn--full"
                  type="button"
                  :disabled="!aiCanAdopt"
                  @click="adoptAiDraft"
                >
                  {{ $t('strategyNew.aiAdoptAction') }}
                </button>

                <div v-if="aiCanAdopt" class="quick-refine">
                  <p class="quick-refine__label">{{ $t('strategyNew.aiQuickRefine') }}</p>
                  <div class="quick-refine__chips">
                    <button v-for="hint in quickRefineHints" :key="hint" class="chip-btn" type="button" @click="applyRefineHint(hint)">{{ hint }}</button>
                  </div>
                </div>
              </div>
            </section>

            <section class="card ai-chat">
              <div ref="aiChatMessages" class="ai-chat__messages">
                <div v-if="aiMessages.length === 0" class="chat-empty">
                  <p class="chat-empty__title">{{ $t('strategyNew.aiChatEmptyTitle') }}</p>
                  <p class="chat-empty__subtitle">{{ $t('strategyNew.aiChatEmptySubtitle') }}</p>
                  <div class="scenario-grid">
                    <button v-for="scenario in scenarios" :key="scenario.key" class="scenario-card" type="button" @click="applyScenario(scenario)">
                      <span class="scenario-card__icon">{{ scenario.icon }}</span>
                      <span class="scenario-card__label">{{ $t(scenario.labelKey) }}</span>
                    </button>
                  </div>
                </div>
                <article
                  v-for="(message, index) in aiMessages"
                  :key="`${message.role}-${index}`"
                  class="chat-bubble"
                  :class="`chat-bubble--${message.role}`"
                >
                  <p class="chat-bubble__role">{{ message.role === 'user' ? $t('strategyNew.aiUserRole') : $t('strategyNew.aiAssistantRole') }}</p>
                  <div class="chat-bubble__content" v-html="renderChatContent(message.content)"></div>
                </article>
                <div v-if="aiSubmitting" class="chat-bubble chat-bubble--assistant chat-bubble--thinking">
                  <p class="chat-bubble__role">{{ $t('strategyNew.aiAssistantRole') }}</p>
                  <div class="thinking-dots">
                    <span class="thinking-dot"></span>
                    <span class="thinking-dot"></span>
                    <span class="thinking-dot"></span>
                  </div>
                </div>
              </div>

              <label class="field ai-chat__composer">
                <span class="field-label">{{ $t('strategyNew.aiPromptLabel') }}</span>
                <textarea
                  v-model="aiPrompt"
                  data-test="ai-prompt"
                  class="field-input field-textarea"
                  :placeholder="$t('strategyNew.aiPromptPlaceholder')"
                  @keydown.enter.ctrl="handleAiSend"
                />
                <span class="field-hint">{{ $t('strategyNew.aiSendShortcut') }}</span>
              </label>
              <div class="actions">
                <button
                  data-test="ai-send"
                  class="btn btn-primary"
                  type="button"
                  :disabled="aiSubmitting || !aiPrompt.trim()"
                  @click="handleAiSend"
                >
                  <span v-if="aiSubmitting" class="btn-spinner"></span>
                  {{ aiSubmitting ? $t('strategyNew.aiSending') : $t('strategyNew.aiSendAction') }}
                </button>
              </div>
              <p v-if="aiError" class="form-message error">{{ aiError }}</p>
            </section>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, h, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import { fetchIntegrations, type UserIntegration } from '../api/integrations'
import { analyzeStrategyImport, generateAiStrategyDraft } from '../api/strategies'
import { strategyTemplates, type StrategyTemplateDefinition } from '../lib/strategyTemplates'
import type { AiStrategyMessage, StrategyImportAnalysis } from '../types/Strategy'
import { QSelect } from '../components/ui'

const { t } = useI18n()
const router = useRouter()

const templates = strategyTemplates
const templatePickerOpen = ref(false)
const aiModalOpen = ref(false)
const isGuideOpen = ref(false)
const templateState = ref({
  loading: false,
  error: '',
})

const aiLoadingIntegrations = ref(false)
const aiIntegrations = ref<UserIntegration[]>([])
const selectedAiIntegrationId = ref('')
const aiMessages = ref<AiStrategyMessage[]>([])
const aiPrompt = ref('')
const aiSubmitting = ref(false)
const aiError = ref('')
const aiLatestAnalysis = ref<StrategyImportAnalysis | null>(null)
const aiChatMessages = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    const el = aiChatMessages.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function validationLabel(value: boolean) {
  return value ? 'Passed' : 'Needs review'
}

function validationClass(value: boolean) {
  return value ? 'validation-state validation-state--pass' : 'validation-state validation-state--warn'
}

const minimalGuideCode = computed(() => `from qysp import Order


def on_bar(ctx, data):
    if data.close > data.open:
        return [Order(symbol=data.symbol, side="buy", volume=1)]
    return []`)

const aiLatestMetadata = computed<Record<string, unknown>>(
  () => (aiLatestAnalysis.value?.metadataCandidates || {}) as Record<string, unknown>
)

const aiCanAdopt = computed(() => {
  const analysis = aiLatestAnalysis.value
  return Boolean(
    analysis &&
      analysis.entrypointCandidates.length > 0 &&
      analysis.errors.length === 0 &&
      analysis.draftImportId
  )
})

const aiIntegrationOptions = computed(() =>
  aiIntegrations.value.map((i) => ({ label: i.displayName, value: i.id }))
)

async function handleTemplateSelect(template: StrategyTemplateDefinition) {
  templateState.value = {
    loading: true,
    error: '',
  }
  try {
    const file = new File([template.code], template.filename, { type: 'text/x-python' })
    const analysis = await analyzeStrategyImport(file)
    sessionStorage.setItem(
      `strategy-import:${analysis.draftImportId}`,
      JSON.stringify({
        ...analysis,
        metadataCandidates: {
          ...(analysis.metadataCandidates || {}),
          name: template.defaultName,
          symbol: (analysis.metadataCandidates?.symbol as string) || template.defaultSymbol,
          category: (analysis.metadataCandidates?.category as string) || template.category,
          tags: Array.isArray(analysis.metadataCandidates?.tags) && analysis.metadataCandidates?.tags.length
            ? analysis.metadataCandidates?.tags
            : template.tags,
        },
      })
    )
    templatePickerOpen.value = false
    await router.push({
      name: 'strategy-import-confirm',
      query: {
        draftImportId: analysis.draftImportId,
        source: 'template',
        template: template.slug,
      },
    })
  } catch (error: any) {
    templateState.value.error = error?.message || t('strategyNew.templateError')
  } finally {
    templateState.value.loading = false
  }
}

async function openAiBuilder() {
  aiModalOpen.value = true
  aiError.value = ''
  await loadAiIntegrations()
}

async function loadAiIntegrations() {
  aiLoadingIntegrations.value = true
  try {
    const integrations = await fetchIntegrations()
    aiIntegrations.value = integrations.filter((item) => item.providerKey === 'openai_compatible')
    if (!selectedAiIntegrationId.value && aiIntegrations.value.length > 0) {
      selectedAiIntegrationId.value = aiIntegrations.value[0].id
    }
  } catch (error: any) {
    aiError.value = error?.message || t('strategyNew.aiError')
  } finally {
    aiLoadingIntegrations.value = false
  }
}

function openAiSettings() {
  router.push({
    path: '/settings',
    query: {
      provider: 'openai_compatible',
      redirect: '/strategies/new',
    },
  })
}

async function handleAiSend() {
  if (!selectedAiIntegrationId.value) {
    aiError.value = t('strategyNew.aiSelectIntegration')
    return
  }
  if (!aiPrompt.value.trim()) {
    return
  }

  aiSubmitting.value = true
  aiError.value = ''
  const pendingMessages: AiStrategyMessage[] = [...aiMessages.value, { role: 'user', content: aiPrompt.value.trim() }]
  aiMessages.value = pendingMessages
  const currentPrompt = aiPrompt.value
  aiPrompt.value = ''
  scrollToBottom()

  try {
    const result = await generateAiStrategyDraft({
      integrationId: selectedAiIntegrationId.value,
      messages: pendingMessages,
    })
    aiMessages.value = [...pendingMessages, { role: 'assistant', content: result.reply }]
    aiLatestAnalysis.value = result.analysis
    scrollToBottom()
  } catch (error: any) {
    aiPrompt.value = currentPrompt
    aiError.value = error?.message || t('strategyNew.aiError')
  } finally {
    aiSubmitting.value = false
  }
}

async function adoptAiDraft() {
  if (!aiLatestAnalysis.value?.draftImportId) {
    return
  }
  sessionStorage.setItem(`strategy-import:${aiLatestAnalysis.value.draftImportId}`, JSON.stringify(aiLatestAnalysis.value))
  aiModalOpen.value = false
  await router.push({
    name: 'strategy-preview',
    query: {
      draftImportId: aiLatestAnalysis.value.draftImportId,
      source: 'ai',
    },
  })
}

const scenarios = [
  { key: 'bullish', icon: '📈', labelKey: 'strategyNew.scenarioBullish', prompt: t('strategyNew.scenarioBullishPrompt') },
  { key: 'bearish', icon: '📉', labelKey: 'strategyNew.scenarioBearish', prompt: t('strategyNew.scenarioBearishPrompt') },
  { key: 'reversal', icon: '🔄', labelKey: 'strategyNew.scenarioReversal', prompt: t('strategyNew.scenarioReversalPrompt') },
  { key: 'trend', icon: '🏄', labelKey: 'strategyNew.scenarioTrend', prompt: t('strategyNew.scenarioTrendPrompt') },
  { key: 'learn', icon: '🎓', labelKey: 'strategyNew.scenarioLearn', prompt: t('strategyNew.scenarioLearnPrompt') },
]

const quickRefineHints = computed(() => [
  t('strategyNew.refineAdjustStop'),
  t('strategyNew.refineChangeSymbol'),
  t('strategyNew.refineOptimize'),
  t('strategyNew.refineAddFilter'),
])

function applyScenario(scenario: typeof scenarios[number]) {
  aiPrompt.value = scenario.prompt
}

function applyRefineHint(hint: string) {
  aiPrompt.value = hint
}

function formatCategory(cat: string): string {
  const map: Record<string, string> = {
    'trend-following': t('strategyPreview.catTrendFollowing'),
    'mean-reversion': t('strategyPreview.catMeanReversion'),
    momentum: t('strategyPreview.catMomentum'),
    'multi-indicator': t('strategyPreview.catMultiIndicator'),
    other: t('strategyPreview.catOther'),
  }
  return map[cat] || cat
}

function riskLevelLabel(level: string): string {
  const map: Record<string, string> = {
    low: t('strategyPreview.riskLow'),
    medium: t('strategyPreview.riskMedium'),
    high: t('strategyPreview.riskHigh'),
  }
  return map[level] || level
}

function renderChatContent(content: string): string {
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
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
.new-strategy-view {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  margin: 0;
}

.path-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

/* AI card spans full row */
.path-card--ai {
  grid-column: 1 / -1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: var(--spacing-xxl);
  min-height: 250px;
  padding: 34px 40px;
  cursor: pointer;
  border: 2px solid var(--color-border-strong);
  background:
    linear-gradient(100deg, rgba(249, 168, 37, 0.20) 0%, rgba(249, 168, 37, 0.08) 32%, rgba(25, 118, 210, 0.10) 74%, rgba(25, 118, 210, 0.16) 100%),
    linear-gradient(180deg, #ffffff 0%, #fbfaf5 100%);
  box-shadow: 8px 8px 0 rgba(17, 17, 17, 0.10);
  transition: transform var(--transition-normal), box-shadow var(--transition-normal), border-color var(--transition-normal);
}

.path-card--ai:hover {
  transform: translate(-2px, -2px);
  border-color: var(--color-accent);
  box-shadow: 12px 12px 0 rgba(17, 17, 17, 0.14);
}

.path-card--ai__glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 34%;
  height: 100%;
  border-radius: 0;
  background:
    linear-gradient(135deg, rgba(25, 118, 210, 0.18), rgba(249, 168, 37, 0.10)),
    repeating-linear-gradient(135deg, rgba(17, 17, 17, 0.08) 0 1px, transparent 1px 14px);
  clip-path: polygon(28% 0, 100% 0, 100% 100%, 0 100%);
  pointer-events: none;
}

.path-card--ai__content {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxl);
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.path-card--ai__content .path-card__header {
  flex: 1;
  min-width: 0;
}

.path-card--ai__content .path-card__body {
  flex: 0 1 430px;
  min-width: 0;
}

.path-card--ai__badge-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.path-card--ai__spark {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 2px solid var(--color-border-strong);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-accent);
  animation: sparkle 3s ease-in-out infinite;
}

.path-card--ai__action {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  align-self: flex-end;
}

.path-card--ai .btn-primary {
  min-height: 48px;
  padding: 0 20px;
  border-width: 2px;
  border-radius: var(--radius-full);
  background: var(--color-text-primary);
  border-color: #000000;
  color: #fff;
  font-size: var(--font-size-lg);
  font-weight: 800;
  box-shadow: 4px 4px 0 rgba(249, 168, 37, 0.95);
}

.path-card--ai .btn-primary:hover {
  background: var(--color-accent);
  border-color: #000000;
  color: var(--color-text-primary);
  box-shadow: 5px 5px 0 rgba(17, 17, 17, 0.22);
}

@keyframes sparkle {
  0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
  50% { opacity: 0.7; transform: scale(1.15) rotate(15deg); }
}

.path-card {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.path-card__header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.path-card__header h2,
.path-card__header p,
.guide-eyebrow,
.guide-toggle h2,
.template-card h3,
.template-card p,
.guide-section h3,
.guide-section p,
.guide-toggle__hint,
.chat-bubble__content,
.chat-bubble__role {
  margin: 0;
}

.path-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.path-card--ai .path-card__header {
  gap: 12px;
}

.path-card--ai .path-card__header h2 {
  max-width: 420px;
  font-family: var(--font-zh-display);
  font-size: clamp(30px, 3.2vw, 46px);
  line-height: 1.08;
  font-weight: 900;
  color: var(--color-text-primary);
}

.path-card--ai .path-card__body {
  padding: 18px 20px;
  border: 2px solid rgba(17, 17, 17, 0.16);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-sm);
}

.path-card__description {
  margin: 0;
  font-size: var(--font-size-sm);
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.path-card--ai .path-card__description {
  max-width: 680px;
  font-size: var(--font-size-lg);
  line-height: 1.75;
  color: #2f2f2f;
}

.path-badge {
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(25, 118, 210, 0.10);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.path-badge--accent {
  border: 2px solid var(--color-border-strong);
  background: var(--color-text-primary);
  color: var(--color-accent);
}

.path-checklist,
.guide-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.path-check {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.path-check::before {
  content: '•';
  margin-right: 8px;
  color: var(--color-accent);
}

.path-card--ai .path-check {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: var(--color-text-primary);
  line-height: 1.55;
}

.path-card--ai .path-check::before {
  content: '✓';
  display: grid;
  place-items: center;
  flex: 0 0 18px;
  width: 18px;
  height: 18px;
  margin: 1px 0 0;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-text-primary);
  font-size: 11px;
  font-weight: 900;
}

.ai-highlight-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 620px;
}

.ai-tag {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: 800;
  border: 1px solid rgba(249, 168, 37, 0.45);
  background: rgba(255, 250, 235, 0.88);
  color: #8a5200;
  letter-spacing: 0;
}

.ai-learn-more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-sm);
  color: var(--color-primary-dark);
  text-decoration: none;
  font-weight: 800;
  transition: opacity 0.2s;
}

.ai-learn-more:hover {
  opacity: 0.8;
}

.import-visual {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.import-visual__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: var(--color-primary-bg);
  color: var(--color-accent);
}

.import-visual__text,
.guide-toggle__hint,
.guide-section p,
.field-hint,
.summary-label {
  color: var(--color-text-muted);
}

.tag-row {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.pill {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.pill--accent {
  color: var(--color-accent);
}

.guide-card {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
}

.guide-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.guide-toggle__copy {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.guide-eyebrow {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.guide-toggle__icon {
  font-size: 1.4rem;
  transition: transform 0.2s ease;
}

.guide-toggle__icon--open {
  transform: rotate(180deg);
}

.guide-content {
  margin-top: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-lg);
}

.guide-list {
  margin: var(--spacing-sm) 0 0;
  padding-left: 18px;
}

.guide-list--ordered {
  list-style: decimal;
}

.guide-code {
  margin: 0;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(7, 17, 27, 0.94);
  color: #f8fbff;
  overflow-x: auto;
}

.guide-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.overlay-backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: rgba(12, 18, 32, 0.55);
  backdrop-filter: blur(6px);
  z-index: 40;
  animation: modalOverlayIn 200ms ease both;
}

.template-picker,
.ai-builder {
  width: min(1080px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding: var(--spacing-lg);
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  animation: modalCardIn 300ms cubic-bezier(0.2, 0, 0, 1) both;
}

.template-picker__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.template-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  padding: var(--spacing-lg);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-accent);
  box-shadow: var(--shadow-md);
}

.template-card p {
  color: var(--color-text-muted);
}

.ai-builder__grid {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  gap: var(--spacing-lg);
}

.ai-sidepanel {
  display: grid;
  gap: var(--spacing-md);
}

.ai-panel,
.ai-chat {
  padding: var(--spacing-lg);
}

.ai-chat {
  display: grid;
  gap: var(--spacing-md);
}

.ai-chat__messages {
  min-height: 320px;
  max-height: 480px;
  overflow: auto;
  display: grid;
  gap: var(--spacing-sm);
  padding-right: var(--spacing-xs);
}

.chat-bubble {
  max-width: 88%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-lg);
  display: grid;
  gap: 6px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  line-height: 1.6;
  letter-spacing: 0.01em;
}

.chat-bubble--user {
  justify-self: end;
  background: rgba(64, 162, 255, 0.12);
  border: 1px solid rgba(64, 162, 255, 0.18);
}

.chat-bubble--assistant {
  justify-self: start;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--color-border);
}

.chat-bubble__role {
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 600;
}

.chat-bubble__content {
  font-size: var(--font-size-md);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-panel {
  display: grid;
  place-items: center;
  min-height: 160px;
  color: var(--color-text-muted);
  text-align: center;
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.field-label {
  font-size: var(--font-size-sm);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field-textarea {
  min-height: 120px;
  resize: vertical;
}

.summary-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row,
.actions {
  display: flex;
  align-items: center;
}

.summary-row {
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.summary-value {
  text-align: right;
}

.summary-alert {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
}

.summary-alert--warning {
  background: rgba(200, 122, 0, 0.12);
  color: #c87a00;
}

.summary-alert--error {
  background: rgba(207, 78, 78, 0.12);
  color: #cf4e4e;
}

.actions {
  justify-content: flex-start;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

.form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.error {
  color: var(--color-danger);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.chat-bubble--thinking {
  min-width: 80px;
}

.thinking-dots {
  display: flex;
  gap: 5px;
  padding: 6px 0;
}

.thinking-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--color-text-muted);
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.thinking-dot:nth-child(2) {
  animation-delay: 0.16s;
}

.thinking-dot:nth-child(3) {
  animation-delay: 0.32s;
}

.preview-file {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
}

.preview-file__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.preview-file__name {
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace);
  font-size: var(--font-size-xs);
  color: var(--color-accent);
}

.validation-block {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.validation-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
}

.validation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.validation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.validation-state--pass {
  color: #2a9d65;
}

.validation-state--warn {
  color: #c87a00;
}

@media (max-width: 900px) {
  .path-grid {
    grid-template-columns: 1fr;
  }

  .path-card--ai {
    flex-direction: column;
    align-items: stretch;
  }

  .path-card--ai__content {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }

  .path-card--ai__action {
    align-self: flex-start;
  }

  .guide-grid,
  .template-grid,
  .ai-builder__grid {
    grid-template-columns: 1fr;
  }
}

/* Chat empty state */
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) 0;
  text-align: center;
}

.chat-empty__title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.chat-empty__subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
}

/* Scenario cards */
.scenario-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  justify-content: center;
}

.scenario-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.15s;
}

.scenario-card:hover {
  border-color: var(--color-accent);
  background: rgba(64, 162, 255, 0.06);
  transform: translateY(-1px);
}

.scenario-card__icon {
  font-size: var(--font-size-md);
  line-height: 1;
}

.scenario-card__label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Draft section in sidepanel */
.draft-section {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.draft-section__title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.draft-section__text {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Param chips */
.param-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.param-chip {
  padding: 2px 8px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.05);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', Consolas, monospace);
}

/* Risk badge */
.risk-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.risk-badge--low {
  background: rgba(42, 157, 101, 0.15);
  color: #2a9d65;
}

.risk-badge--medium {
  background: rgba(200, 122, 0, 0.15);
  color: #c87a00;
}

.risk-badge--high {
  background: rgba(207, 78, 78, 0.15);
  color: #cf4e4e;
}

/* Quick refine */
.quick-refine {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.quick-refine__label {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
}

.quick-refine__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip-btn {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.chip-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* Full-width button */
.btn--full {
  width: 100%;
  margin-top: var(--spacing-md);
}

/* Chat bubble code/strong */
.chat-bubble__content :deep(code) {
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.08);
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', Consolas, monospace);
  font-size: 0.9em;
}

.chat-bubble__content :deep(strong) {
  font-weight: 600;
  color: var(--color-text-primary);
}

@media (max-width: 720px) {
  .page-header,
  .template-picker__header {
    flex-direction: column;
  }

  .chat-bubble {
    max-width: 100%;
  }

  .scenario-grid {
    flex-direction: column;
    align-items: stretch;
  }

  .scenario-card {
    justify-content: center;
  }
}
</style>
