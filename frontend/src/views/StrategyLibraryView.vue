<template>
  <section class="strategy-library">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ t('strategy.library.pageTitle') }}</h1>
          <p class="page-subtitle">{{ t('strategy.library.pageSubtitle') }}</p>
        </div>
        <div class="header-actions">
          <RouterLink class="btn btn-primary" to="/strategies/import">
            {{ t('strategy.library.openImportWizard') }}
          </RouterLink>
          <RouterLink class="btn btn-secondary" to="/">
            {{ t('strategy.library.backToDashboard') }}
          </RouterLink>
        </div>
      </div>

      <section v-if="isGuidedMode" :class="['card guided-card', { 'onboarding-highlight': userStore.onboardingHighlightTarget === 'guided-strategy-card' }]" data-onboarding-target="guided-strategy-card">
        <div class="section-header">
          <h2>{{ t('strategy.library.guidedStrategy') }}</h2>
          <p>{{ t('strategy.library.guidedStrategyDesc') }}</p>
        </div>
        <div v-if="guidedLoading" class="empty-state">{{ t('strategy.library.loadingGuided') }}</div>
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
                {{ t('strategy.library.viewDetails') }}
              </button>
              <button class="btn btn-primary" type="button" @click="handleGuidedSelect(strategy.id)">
                {{ t('strategy.library.useThisStrategy') }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <div class="layout-grid">
        <div class="card import-card">
          <div class="section-header">
            <h2>{{ t('strategy.library.importStrategy') }}</h2>
            <p>{{ t('strategy.library.importStrategyDesc') }}</p>
          </div>
          <div class="import-format-list">
            <span class="pill">strategy.py</span>
            <span class="pill">source zip</span>
            <span class="pill">.qys package</span>
          </div>
          <p class="import-note">
            {{ t('strategy.library.importNote') }}
          </p>
          <div class="actions">
            <button
              class="btn btn-primary"
              type="button"
              data-test="open-import-wizard"
              @click="handleOpenImportWizard"
            >
              {{ t('strategy.library.openImportWizard') }}
            </button>
          </div>
        </div>

        <div class="card library-card">
          <div class="section-header">
            <h2>{{ t('strategy.library.myStrategies') }}</h2>
            <p>{{ t('strategy.library.itemCount', { count: total, plural: total !== 1 ? 's' : '' }) }}</p>
          </div>

          <div v-if="loading" class="empty-state">{{ t('strategy.library.loadingLibrary') }}</div>
          <p v-else-if="loadError" class="message error">{{ loadError }}</p>
          <div v-else-if="items.length === 0" class="empty-state">{{ t('strategy.library.noStrategies') }}</div>
          <div v-else class="strategy-list">
            <article v-for="strategy in items" :key="strategy.id" class="strategy-row">
              <div class="row-main">
                <div class="row-title">{{ strategy.title || strategy.name }}</div>
                <div class="row-meta">
                  <span>{{ strategy.category || 'other' }}</span>
                  <span>{{ strategy.source || 'upload' }}</span>
                  <span
                    class="status-pill"
                    :class="statusClass(strategy.reviewStatus)"
                    :data-test="`publish-status-${strategy.id}`"
                  >
                    {{ publishStatusLabel(strategy.reviewStatus) }}
                  </span>
                  <span>{{ formatCreatedAt(strategy.createdAt) }}</span>
                </div>
                <p class="row-description">{{ strategy.description || t('strategy.library.noDescription') }}</p>
                <div class="tag-row">
                  <span v-for="tag in strategy.tags" :key="tag" class="pill">{{ tag }}</span>
                </div>
              </div>
              <div class="row-actions">
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
                  class="btn btn-secondary danger"
                  type="button"
                  :data-test="`delete-${strategy.id}`"
                  @click="handleDelete(strategy.id)"
                >
                  {{ t('strategy.library.delete') }}
                </button>
              </div>
            </article>
          </div>

          <div class="pagination">
            <button class="btn btn-secondary" type="button" :disabled="page <= 1 || loading" @click="changePage(page - 1)">
              {{ t('strategy.library.previous') }}
            </button>
            <span>Page {{ page }} / {{ totalPages }}</span>
            <button
              class="btn btn-secondary"
              type="button"
              :disabled="page >= totalPages || loading"
              @click="changePage(page + 1)"
            >
              {{ t('strategy.library.next') }}
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
.strategy-library {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
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

.actions {
  margin-top: var(--spacing-md);
}

.import-format-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-lg);
}

.import-note,
.row-title {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-secondary);
}

.row-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

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

.row-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--spacing-sm);
  min-width: 180px;
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

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.status-draft {
  background: rgba(100, 116, 139, 0.12);
  color: var(--color-text-muted);
}

.status-pending {
  background: var(--color-accent-bg);
  color: var(--color-warning);
}

.status-approved {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-rejected {
  background: var(--color-danger-bg);
  color: var(--color-danger);
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
  .guided-actions,
  .row-actions,
  .header-actions {
    display: flex;
    flex-direction: column;
  }
}
</style>
