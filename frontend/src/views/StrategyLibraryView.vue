<template>
  <section class="strategy-library">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">策略管理</p>
          <h1 class="page-title">{{ t('strategy.library.pageTitle') }}</h1>
          <p class="page-subtitle">{{ t('strategy.library.pageSubtitle') }}</p>
        </div>
        <div class="header-actions">
          <RouterLink class="btn btn-secondary" to="/">
            {{ t('strategy.library.backToDashboard') }}
          </RouterLink>
          <RouterLink class="btn btn-primary" to="/strategies/import">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            {{ t('strategy.library.openImportWizard') }}
          </RouterLink>
        </div>
      </div>

      <!-- Guided Mode Section -->
      <section
        v-if="isGuidedMode"
        :class="['guided-section', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'guided-strategy-card' }]"
        data-onboarding-target="guided-strategy-card"
      >
        <div class="guided-section__header">
          <div class="guided-section__icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
          </div>
          <div>
            <h2 class="section-title">{{ t('strategy.library.guidedStrategy') }}</h2>
            <p class="section-subtitle">{{ t('strategy.library.guidedStrategyDesc') }}</p>
          </div>
        </div>

        <div v-if="guidedLoading" class="empty-state">
          <div class="empty-state__spinner"></div>
          {{ t('strategy.library.loadingGuided') }}
        </div>
        <p v-else-if="guidedError" class="message error">{{ guidedError }}</p>
        <div v-else-if="guidedStrategies.length" class="strategy-list">
          <article v-for="strategy in guidedStrategies" :key="strategy.id" class="strategy-card strategy-card--featured">
            <div class="strategy-card__body">
              <div class="strategy-card__name">{{ strategy.name }}</div>
              <div class="strategy-card__meta">
                <span class="meta-pill">{{ strategy.symbol }}</span>
                <span class="meta-pill meta-pill--accent">{{ strategy.category || 'beginner' }}</span>
              </div>
              <div v-if="strategy.tags?.length" class="tag-row">
                <span v-for="tag in strategy.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
            <div class="strategy-card__actions">
              <button class="btn btn-secondary" type="button" @click="handleGuidedPreview(strategy.id)">
                {{ t('strategy.library.viewDetails') }}
              </button>
              <button class="btn btn-primary" type="button" @click="handleGuidedSelect(strategy.id)">
                {{ t('strategy.library.useThisStrategy') }}
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </button>
            </div>
          </article>
        </div>
      </section>

      <div class="layout-grid">
        <!-- Import Card -->
        <div class="card panel-card">
          <div class="panel-card__header">
            <div class="panel-card__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <div>
              <h2 class="section-title">{{ t('strategy.library.importStrategy') }}</h2>
              <p class="section-subtitle">{{ t('strategy.library.importStrategyDesc') }}</p>
            </div>
          </div>

          <div class="format-group">
            <p class="format-group__label">支持格式</p>
            <div class="format-list">
              <span class="format-pill">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                strategy.py
              </span>
              <span class="format-pill">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
                source zip
              </span>
              <span class="format-pill format-pill--accent">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                .qys package
              </span>
            </div>
          </div>

          <p class="import-note">{{ t('strategy.library.importNote') }}</p>

          <button
            class="btn btn-primary btn--full"
            type="button"
            data-test="open-import-wizard"
            @click="handleOpenImportWizard"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            {{ t('strategy.library.openImportWizard') }}
          </button>
        </div>

        <!-- Library Card -->
        <div class="card panel-card">
          <div class="panel-card__header">
            <div class="panel-card__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div style="flex:1">
              <div class="section-header-row">
                <h2 class="section-title">{{ t('strategy.library.myStrategies') }}</h2>
                <span class="count-badge">{{ total }}</span>
              </div>
              <p class="section-subtitle">{{ t('strategy.library.itemCount', { count: total, plural: total !== 1 ? 's' : '' }) }}</p>
            </div>
          </div>

          <div v-if="loading" class="empty-state">
            <div class="empty-state__spinner"></div>
            {{ t('strategy.library.loadingLibrary') }}
          </div>
          <p v-else-if="loadError" class="message error">{{ loadError }}</p>
          <div v-else-if="items.length === 0" class="empty-state empty-state--dashed">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>
            {{ t('strategy.library.noStrategies') }}
          </div>
          <div v-else class="strategy-list">
            <article v-for="strategy in items" :key="strategy.id" class="strategy-card">
              <div class="strategy-card__body">
                <div class="strategy-card__name-row">
                  <span class="strategy-card__name">{{ strategy.title || strategy.name }}</span>
                  <span
                    class="status-badge"
                    :class="statusClass(strategy.reviewStatus)"
                    :data-test="`publish-status-${strategy.id}`"
                  >
                    <span class="status-badge__dot"></span>
                    {{ publishStatusLabel(strategy.reviewStatus) }}
                  </span>
                </div>
                <div class="strategy-card__meta">
                  <span class="meta-item">{{ strategy.category || 'other' }}</span>
                  <span class="meta-divider">·</span>
                  <span class="meta-item">{{ strategy.source || 'upload' }}</span>
                  <span class="meta-divider">·</span>
                  <span class="meta-item">{{ formatCreatedAt(strategy.createdAt) }}</span>
                </div>
                <p class="strategy-card__desc">{{ strategy.description || t('strategy.library.noDescription') }}</p>
                <div v-if="strategy.tags?.length" class="tag-row">
                  <span v-for="tag in strategy.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
              <div class="strategy-card__actions">
                <button
                  class="btn btn-secondary"
                  type="button"
                  :data-test="`publish-open-${strategy.id}`"
                  :disabled="isPublishDisabled(strategy.reviewStatus)"
                  @click="openPublishFlow(strategy)"
                >
                  {{ publishButtonLabel(strategy.reviewStatus) }}
                </button>
                <button
                  class="btn btn-ghost btn--danger"
                  type="button"
                  :data-test="`delete-${strategy.id}`"
                  @click="handleDelete(strategy.id)"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                  {{ t('strategy.library.delete') }}
                </button>
              </div>
            </article>
          </div>

          <div class="pagination">
            <button class="btn btn-ghost" type="button" :disabled="page <= 1 || loading" @click="changePage(page - 1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
              {{ t('strategy.library.previous') }}
            </button>
            <span class="pagination__info">{{ page }} / {{ totalPages }}</span>
            <button
              class="btn btn-ghost"
              type="button"
              :disabled="page >= totalPages || loading"
              @click="changePage(page + 1)"
            >
              {{ t('strategy.library.next') }}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <StrategyPublishFlow
      :open="publishOpen"
      :strategy="selectedStrategy"
      :submitting="publishSubmitting"
      :submitted="publishSubmitted"
      :submit-error="publishError"
      @close="closePublishFlow"
      @submit="handlePublishSubmit"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import StrategyPublishFlow from '../components/strategy/StrategyPublishFlow.vue'
import { deleteStrategy, fetchMarketplaceStrategies, fetchStrategies } from '../api/strategies'
import type { MarketplacePublishPayload, MarketplaceReviewStatus, Strategy } from '../types/Strategy'
import { useMarketplaceStore, useUserStore } from '../stores'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const marketplaceStore = useMarketplaceStore()

const items = ref<Strategy[]>([])
const guidedStrategies = ref<Strategy[]>([])
const loading = ref(false)
const loadError = ref('')
const guidedLoading = ref(false)
const guidedError = ref('')
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const publishOpen = ref(false)
const publishSubmitting = ref(false)
const publishSubmitted = ref(false)
const publishError = ref('')
const selectedStrategy = ref<Strategy | null>(null)

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
    items.value = result.items.map((item) => ({
      ...item,
      reviewStatus: item.reviewStatus || 'draft',
      isPublic: Boolean(item.isPublic),
    }))
    page.value = result.page
    perPage.value = result.perPage
    total.value = result.total
  } catch (error: any) {
    loadError.value = error?.message || t('strategy.library.failedToLoadLibrary')
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
    guidedError.value = error?.message || t('strategy.library.failedToLoadGuided')
  } finally {
    guidedLoading.value = false
  }
}

async function handleOpenImportWizard() {
  await router.push('/strategies/import')
}

async function handleDelete(strategyId: string) {
  if (!window.confirm(t('strategy.library.deleteConfirm'))) {
    return
  }

  await deleteStrategy(strategyId)
  const fallbackPage = items.value.length === 1 && page.value > 1 ? page.value - 1 : page.value
  await loadPage(fallbackPage)
}

function openPublishFlow(strategy: Strategy) {
  selectedStrategy.value = strategy
  publishOpen.value = true
  publishSubmitting.value = false
  publishSubmitted.value = false
  publishError.value = ''
}

function closePublishFlow() {
  publishOpen.value = false
  publishSubmitting.value = false
  publishSubmitted.value = false
  publishError.value = ''
  selectedStrategy.value = null
}

async function handlePublishSubmit(payload: MarketplacePublishPayload) {
  publishSubmitting.value = true
  publishError.value = ''
  try {
    const result = await marketplaceStore.publishStrategy(payload)
    const latestStatus = await marketplaceStore.getPublishStatus(payload.strategyId)
    items.value = items.value.map((item) =>
      item.id === payload.strategyId
        ? {
            ...item,
            title: payload.title,
            description: payload.description,
            tags: payload.tags,
            category: payload.category,
            reviewStatus: latestStatus.reviewStatus || result.reviewStatus,
            isPublic: latestStatus.isPublic,
          }
        : item
    )
    selectedStrategy.value = items.value.find((item) => item.id === payload.strategyId) || selectedStrategy.value
    publishSubmitted.value = true
  } catch (error: any) {
    publishError.value = error?.message || t('strategy.library.failedToSubmit')
  } finally {
    publishSubmitting.value = false
  }
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
    name: 'marketplace-strategy-detail',
    params: { strategyId },
  })
}

function formatCreatedAt(value?: string | number) {
  if (!value) return t('strategy.library.unknownTime')
  const numeric = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(numeric)) return String(value)
  return new Date(numeric).toLocaleDateString()
}

function publishStatusLabel(status?: MarketplaceReviewStatus) {
  if (status === 'pending') return t('strategy.library.pendingReview')
  if (status === 'approved') return t('strategy.library.approved')
  if (status === 'rejected') return t('strategy.library.rejected')
  return t('strategy.library.notPublished')
}

function publishButtonLabel(status?: MarketplaceReviewStatus) {
  return status === 'rejected' ? t('strategy.library.resubmit') : t('strategy.library.publishToMarketplace')
}

function isPublishDisabled(status?: MarketplaceReviewStatus) {
  return status === 'pending' || status === 'approved'
}

function statusClass(status?: MarketplaceReviewStatus) {
  if (status === 'pending') return 'status-pending'
  if (status === 'approved') return 'status-approved'
  if (status === 'rejected') return 'status-rejected'
  return 'status-draft'
}
</script>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.strategy-library {
  width: 100%;
}

/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
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
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  flex-shrink: 0;
}

/* ── Guided Section ── */
.guided-section {
  background: var(--color-surface);
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  position: relative;
  overflow: hidden;
}

.guided-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
}

.guided-section__header {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.guided-section__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  flex-shrink: 0;
}

/* ── Grid Layout ── */
.layout-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.85fr) minmax(0, 1.15fr);
  gap: var(--spacing-lg);
  align-items: start;
}

/* ── Panel Cards ── */
.panel-card {
  padding: 0;
  overflow: hidden;
}

.panel-card__header {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.panel-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-accent);
  flex-shrink: 0;
  margin-top: 2px;
}

.section-header-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
}

.section-subtitle {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: var(--color-primary-bg);
  color: var(--color-accent);
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* ── Format Group ── */
.format-group {
  padding: var(--spacing-md) var(--spacing-lg) 0;
}

.format-group__label {
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin: 0 0 var(--spacing-sm);
}

.format-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.format-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-family: 'Space Mono', monospace;
}

.format-pill--accent {
  border-color: var(--color-primary-border);
  color: var(--color-accent);
  background: var(--color-primary-bg);
}

.import-note {
  margin: var(--spacing-md) var(--spacing-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.btn--full {
  width: calc(100% - var(--spacing-xl));
  margin: 0 var(--spacing-lg) var(--spacing-lg);
  justify-content: center;
}

/* ── Strategy Cards ── */
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.strategy-card {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  transition: background 0.15s;
  animation: slide-up 0.2s ease both;
}

.strategy-card:last-child {
  border-bottom: none;
}

.strategy-card:hover {
  background: var(--color-surface-hover);
}

.strategy-card--featured {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
}

.strategy-card--featured:last-child {
  border-bottom: 1px solid var(--color-primary-border);
  margin-bottom: 0;
}

.strategy-card__body {
  flex: 1;
  min-width: 0;
}

.strategy-card__name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.strategy-card__name {
  font-weight: 700;
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
}

.strategy-card__meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 5px;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.meta-item {
  color: var(--color-text-muted);
}

.meta-divider {
  color: var(--color-border-strong);
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--color-surface-active);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.meta-pill--accent {
  background: var(--color-primary-bg);
  color: var(--color-accent);
}

.strategy-card__desc {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.strategy-card__actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--spacing-xs);
  min-width: 160px;
  justify-content: center;
}

/* ── Tags ── */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: var(--spacing-sm);
}

.tag {
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--color-background);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-muted);
  font-size: 11px;
}

/* ── Status Badges ── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.status-badge__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.status-draft {
  background: rgba(100, 116, 139, 0.1);
  color: var(--color-text-muted);
}

.status-pending {
  background: rgba(245, 158, 11, 0.12);
  color: var(--color-warning);
}

.status-approved {
  background: rgba(16, 185, 129, 0.12);
  color: var(--color-success);
}

.status-rejected {
  background: rgba(255, 59, 59, 0.12);
  color: var(--color-danger);
}

/* ── Ghost Button ── */
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.btn-ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn--danger {
  color: var(--color-danger);
  border-color: transparent;
}

.btn--danger:hover:not(:disabled) {
  background: rgba(255, 59, 59, 0.08);
  border-color: rgba(255, 59, 59, 0.2);
  color: var(--color-danger);
}

/* ── Pagination ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.pagination__info {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

/* ── Empty State ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

.empty-state--dashed {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  margin: var(--spacing-md) var(--spacing-lg);
}

.empty-state__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.message.error {
  padding: var(--spacing-md) var(--spacing-lg);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .layout-grid {
    grid-template-columns: 1fr;
  }

  .strategy-card {
    flex-direction: column;
  }

  .strategy-card__actions {
    flex-direction: row;
    min-width: unset;
  }
}
</style>
