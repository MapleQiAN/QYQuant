<template>
  <section class="pricing-view">
    <div class="container pricing-page">
      <!-- Bauhaus Header -->
      <header class="page-header fade-in">
        <div class="header-text">
          <p class="eyebrow">{{ t('pages.pricingTitle') }}</p>
          <h1 class="page-title">{{ t('pages.pricingTitle') }}</h1>
          <p class="page-subtitle">{{ t('pages.pricingDescription') }}</p>
        </div>
        <div class="header-deco" aria-hidden="true">
          <span class="deco-circle" />
          <span class="deco-triangle" />
        </div>
      </header>

      <!-- Loading / Error states -->
      <p v-if="loading" class="message fade-in">{{ t('pricing.loadingPlans') }}</p>
      <template v-else>
        <p v-if="!isLoggedIn" class="message login-hint fade-in">{{ t('pricing.loginHint') }}</p>
        <p v-else-if="loadError" class="message error fade-in">{{ loadError }}</p>
      </template>

      <!-- Subscription Overview -->
      <div v-if="isLoggedIn && !loading && !loadError && quota" class="sub-overview card fade-in-up">
        <div class="sub-overview__left">
          <div class="sub-overview__badge" :class="'sub-overview__badge--' + currentPlanLevel">
            {{ getPlanName(currentPlanLevel) }}
          </div>
          <div class="sub-overview__meta">
            <span class="sub-overview__status">
              <svg width="8" height="8" viewBox="0 0 8 8" fill="none"><circle cx="4" cy="4" r="4" fill="currentColor"/></svg>
              {{ currentPlanStatusLabel }}
            </span>
            <span v-if="subscription?.payment_provider" class="sub-overview__provider">
              {{ formatProvider(subscription.payment_provider) }}
            </span>
          </div>
        </div>
        <div class="sub-overview__right">
          <div class="sub-overview__usage-title">{{ t('pricing.usageDetails.title') }}</div>
          <div class="sub-overview__stats">
            <div class="usage-stat">
              <span class="usage-stat__label">{{ t('pricing.usageDetails.botRemaining') }}</span>
              <strong class="usage-stat__value tnum" data-test="usage-bot-remaining">{{ remainingBotSlots }}</strong>
              <span class="usage-stat__meta">{{ t('pricing.usageDetails.activeBotsMeta', { active: activeBotCount, total: currentBotLimit }) }}</span>
            </div>
            <div class="usage-stat">
              <span class="usage-stat__label">{{ t('pricing.usageDetails.backtestRemaining') }}</span>
              <strong class="usage-stat__value tnum" data-test="usage-backtest-remaining">{{ backtestRemainingLabel }}</strong>
              <span class="usage-stat__meta">{{ t('pricing.usageDetails.backtestsUsedMeta', { used: quota.used_count, total: backtestTotalLabel }) }}</span>
            </div>
            <div class="usage-stat">
              <span class="usage-stat__label">{{ t('pricing.usageDetails.planExpiry') }}</span>
              <strong class="usage-stat__value" data-test="usage-plan-expiry">{{ currentPlanExpiryLabel }}</strong>
              <span class="usage-stat__meta">{{ subscription?.payment_provider ? formatProvider(subscription.payment_provider) : currentPlanStatusLabel }}</span>
            </div>
          </div>
          <div v-if="quota.plan_limit !== 'unlimited'" class="sub-overview__bar">
            <div class="sub-overview__bar-fill" :style="{ width: usagePercentage + '%' }" />
          </div>
        </div>
      </div>

      <!-- Plus Recommendation -->
      <div v-if="isLoggedIn && !loading && !loadError && shouldRecommendPlus" class="plus-rec card card-hover fade-in">
        <div class="plus-rec__icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/>
          </svg>
        </div>
        <div class="plus-rec__text">
          <h3 class="plus-rec__title">{{ t('pricing.plusRec.title') }}</h3>
          <p class="plus-rec__desc">{{ t('pricing.plusRec.description') }}</p>
        </div>
        <button class="btn btn-primary" type="button" @click="goToCheckout('plus')">
          {{ t('pricing.upgradeTo', { name: plusPlanName }) }}
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <!-- Pricing Grid -->
      <div v-if="!loading && (isLoggedIn ? !loadError : true)" class="pricing-grid stagger-in">
        <article
          v-for="plan in plans"
          :key="plan.level"
          class="pricing-card card card-hover"
          :class="{
            'pricing-card--current': currentPlanLevel === plan.level,
            'pricing-card--lower-tier': isLoggedIn && isPlanTierLowerThanCurrent(plan.level) && currentPlanLevel !== plan.level,
            'pricing-card--featured': plan.featured && shouldShowFeatured,
            'pricing-card--ultra': plan.level === 'ultra',
          }"
        >
          <!-- Accent bar -->
          <div class="pricing-card__accent" :class="'pricing-card__accent--' + plan.level" />

          <!-- Badge row -->
          <div class="pricing-card__badges">
            <span v-if="plan.level === 'ultra'" class="badge badge--ultra-vip">
              <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1l2.2 4.5L15 6.3l-3.5 3.4.8 4.8L8 12.2 3.7 14.5l.8-4.8L1 6.3l4.8-.8L8 1z"/></svg>
              VIP
            </span>
            <span v-if="plan.featured && shouldShowFeatured" class="badge badge--featured">{{ t('pricing.featured') }}</span>
            <span v-if="currentPlanLevel === plan.level" class="badge badge--current">{{ t('pricing.currentPlan') }}</span>
          </div>

          <!-- Plan header -->
          <div class="pricing-card__header">
            <p class="pricing-card__name">{{ plan.name }}</p>
            <div v-if="shouldShowPromo(plan)" class="pricing-card__promo-tag">{{ t('pricing.promoTag') }}</div>
            <div class="pricing-card__price-row">
              <span class="pricing-card__currency">&yen;</span>
              <span class="pricing-card__price tnum">{{ shouldShowPromo(plan) ? plan.promoPrice : plan.price }}</span>
              <span class="pricing-card__unit">{{ t('common.perMonthUnit') }}</span>
              <span v-if="shouldShowPromo(plan)" class="pricing-card__original-price tnum">&yen;{{ plan.price }}</span>
            </div>
          </div>

          <div class="pricing-card__quota-stack">
            <div class="pricing-card__quota">
              {{ plan.quota === null ? t('pricing.unlimitedBacktests') : t('pricing.backtestsPerMonth', { quota: plan.quota }) }}
            </div>
            <div class="pricing-card__capacity">{{ t('pricing.botSlots', { count: plan.botLimit }) }}</div>
          </div>

          <p class="pricing-card__description">{{ plan.description }}</p>

          <!-- CTA -->
          <div class="pricing-card__actions">
            <button
              v-if="plan.level !== 'free' && currentPlanLevel !== plan.level && !isPlanTierLowerThanCurrent(plan.level)"
              class="btn"
              :class="plan.featured && shouldShowFeatured ? 'btn-accent' : 'btn-primary'"
              type="button"
              @click="goToCheckout(plan.level)"
            >
              {{ t('pricing.upgradeTo', { name: plan.name }) }}
            </button>
            <div v-else-if="plan.level === 'free' && isPlanTierLowerThanCurrent(plan.level)" class="btn btn-disabled" aria-disabled="true">
              {{ t('subscription.alreadyOwned') }}
            </div>
            <div v-else-if="plan.level !== 'free' && currentPlanLevel !== plan.level && isPlanTierLowerThanCurrent(plan.level)" class="btn btn-disabled" aria-disabled="true">
              {{ t('subscription.alreadyOwned') }}
            </div>
            <div v-else-if="plan.level === 'free'" class="btn btn-disabled" aria-disabled="true">
              {{ t('pricing.freePlan') }}
            </div>
            <div v-else class="btn btn-disabled btn-disabled--current" aria-disabled="true">
              {{ t('pricing.yourCurrentPlan') }}
            </div>
          </div>

          <!-- Divider -->
          <div class="pricing-card__divider" />

          <!-- Features -->
          <ul class="feature-list" role="list">
            <li
              v-for="feature in plan.features"
              :key="feature.text"
              class="feature-item"
              :class="{ 'feature-item--disabled': !feature.included }"
            >
              <span v-if="feature.included" class="feature-icon feature-icon--check" aria-hidden="true">
                <svg viewBox="0 0 16 16" fill="none">
                  <path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
              <span v-else class="feature-icon feature-icon--cross" aria-hidden="true">
                <svg viewBox="0 0 16 16" fill="none">
                  <path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </span>
              <span class="feature-text">{{ feature.text }}</span>
            </li>
          </ul>
        </article>
      </div>

      <!-- Trust Strip -->
      <div class="pricing-trust fade-in">
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <span>{{ t('pricing.trustSecure') }}</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>{{ t('pricing.trustEncrypted') }}</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
          </svg>
          <span>{{ t('pricing.trustFlexible') }}</span>
        </div>
      </div>

      <!-- Order History -->
      <template v-if="isLoggedIn && !loading">
        <div class="pricing-orders card fade-in">
          <div class="orders-header">
            <div class="panel-card__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <h3 class="orders-header__title">{{ t('pricing.orderHistory.title') }}</h3>
          </div>
          <div v-if="orders.length > 0" class="orders-table-wrap">
            <table class="orders-table">
              <thead>
                <tr>
                  <th>{{ t('pricing.orderHistory.orderId') }}</th>
                  <th>{{ t('pricing.orderHistory.plan') }}</th>
                  <th>{{ t('pricing.orderHistory.amount') }}</th>
                  <th>{{ t('pricing.orderHistory.method') }}</th>
                  <th>{{ t('pricing.orderHistory.status') }}</th>
                  <th>{{ t('pricing.orderHistory.time') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="order in orders" :key="order.order_id">
                  <td class="tnum">{{ order.order_id.slice(0, 8) }}</td>
                  <td>{{ getPlanName(order.plan_level) }}</td>
                  <td class="tnum">{{ formatAmount(order.amount) }}</td>
                  <td>{{ formatProvider(order.provider) }}</td>
                  <td>
                    <span class="order-status" :class="'order-status--' + order.status">
                      {{ formatOrderStatus(order.status) }}
                    </span>
                  </td>
                  <td class="tnum">{{ formatDate(order.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="totalPages > 1" class="orders-pagination">
              <button
                class="btn btn-ghost btn--sm"
                :disabled="ordersCurrentPage <= 1"
                type="button"
                @click="loadOrders(ordersCurrentPage - 1)"
              >
                {{ t('pricing.orderHistory.previousPage') }}
              </button>
              <span class="orders-pagination__indicator tnum">
                {{ t('pricing.orderHistory.pageIndicator', { current: ordersCurrentPage, total: totalPages }) }}
              </span>
              <button
                class="btn btn-ghost btn--sm"
                :disabled="ordersCurrentPage >= totalPages"
                type="button"
                @click="loadOrders(ordersCurrentPage + 1)"
              >
                {{ t('pricing.orderHistory.nextPage') }}
              </button>
            </div>
          </div>
          <p v-else class="panel-empty">{{ t('pricing.orderHistory.noOrders') }}</p>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { OrderItem, PlanLevel, SubscriptionResponse } from '../api/payments'
import { fetchMyOrders, fetchMySubscription } from '../api/payments'
import { getSimBots } from '../api/simulation'
import type { SimulationBot } from '../types/Simulation'
import type { UserQuotaResponse } from '../api/users'
import { fetchMyQuota } from '../api/users'
import { buildPlans, PLAN_TIER_ORDER } from '../data/plans'

const { t } = useI18n()
const router = useRouter()
const plans = computed(() => buildPlans(t))

const loading = ref(true)
const loadError = ref('')
const isLoggedIn = ref(false)
const currentPlanLevel = ref<PlanLevel>('free')
const firstPurchaseEligible = ref(true)
const quota = ref<UserQuotaResponse | null>(null)
const subscription = ref<SubscriptionResponse | null>(null)
const simBots = ref<SimulationBot[]>([])
const orders = ref<OrderItem[]>([])
const ordersCurrentPage = ref(1)
const ordersTotal = ref(0)
const ordersPerPage = ref(10)
const themeMode = ref<'dark' | 'light'>('dark')
let themeObserver: MutationObserver | null = null

async function loadQuota() {
  loading.value = true
  loadError.value = ''
  const token = localStorage.getItem('qyquant-token')
  if (!token) {
    isLoggedIn.value = false
    loading.value = false
    return
  }
  isLoggedIn.value = true
  try {
    const data = await fetchMyQuota()
    quota.value = data
    currentPlanLevel.value = data.plan_level as PlanLevel
    firstPurchaseEligible.value = data.first_purchase_eligible
  } catch (error: any) {
    loadError.value = error?.message || String(t('pricing.loadError'))
  } finally {
    loading.value = false
  }
}

async function loadSubscription() {
  try {
    subscription.value = await fetchMySubscription()
  } catch {
    subscription.value = null
  }
}

async function loadOrders(page = 1) {
  try {
    const result = await fetchMyOrders(page, 10)
    orders.value = result.data
    ordersCurrentPage.value = result.meta.page
    ordersTotal.value = result.meta.total
    ordersPerPage.value = result.meta.per_page
  } catch {
    orders.value = []
  }
}

async function loadSimBots() {
  try {
    simBots.value = await getSimBots()
  } catch {
    simBots.value = []
  }
}

const usagePercentage = computed(() => {
  if (!quota.value || quota.value.plan_limit === 'unlimited') return 0
  const limit = quota.value.plan_limit as number
  if (limit === 0) return 0
  return Math.min(Math.round((quota.value.used_count / limit) * 100), 100)
})

const totalPages = computed(() => Math.max(1, Math.ceil(ordersTotal.value / ordersPerPage.value)))
const currentPlan = computed(() => plans.value.find((plan) => plan.level === currentPlanLevel.value) ?? plans.value[0])
const plusPlanName = computed(() => plans.value.find((plan) => plan.level === 'plus')?.name ?? 'Plus')
const currentBotLimit = computed(() => currentPlan.value.botLimit)
const activeBotCount = computed(() => simBots.value.filter((bot) => bot.status === 'active').length)
const remainingBotSlots = computed(() => Math.max(0, currentBotLimit.value - activeBotCount.value))
const backtestTotalLabel = computed(() =>
  quota.value?.plan_limit === 'unlimited' ? t('pricing.usageDetails.unlimited') : String(quota.value?.plan_limit ?? 0)
)
const backtestRemainingLabel = computed(() =>
  quota.value?.remaining === 'unlimited' ? t('pricing.usageDetails.unlimited') : String(quota.value?.remaining ?? 0)
)
const currentPlanStatusLabel = computed(() =>
  currentPlanLevel.value === 'free'
    ? t('pricing.currentSubscription.freeStatus')
    : t('pricing.currentSubscription.activeStatus')
)
const currentPlanExpiryLabel = computed(() => {
  if (subscription.value?.ends_at) {
    return formatDate(subscription.value.ends_at)
  }
  if (currentPlanLevel.value === 'free') {
    return t('pricing.currentSubscription.freePlanExpiry')
  }
  return t('pricing.currentSubscription.noExpiry')
})
const isLightTheme = computed(() => themeMode.value === 'light')

function getPlanName(planLevel: string): string {
  return plans.value.find((plan) => plan.level === planLevel)?.name ?? planLevel
}

function syncThemeMode() {
  if (typeof document === 'undefined') return
  themeMode.value = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
}

function isPlanTierLowerThanCurrent(planLevel: string): boolean {
  const currentTier = PLAN_TIER_ORDER[currentPlanLevel.value] ?? 0
  const planTier = PLAN_TIER_ORDER[planLevel] ?? 0
  return currentTier > planTier
}

const shouldShowFeatured = computed(() => {
  const currentTier = PLAN_TIER_ORDER[currentPlanLevel.value] ?? 0
  return currentTier < PLAN_TIER_ORDER['plus']
})

const shouldRecommendPlus = computed(() => {
  const currentTier = PLAN_TIER_ORDER[currentPlanLevel.value] ?? 0
  return currentTier < PLAN_TIER_ORDER['plus']
})

function shouldShowPromo(plan: { promoPrice?: number }) {
  if (plan.promoPrice == null) return false
  if (!isLoggedIn.value) return true
  return firstPurchaseEligible.value && currentPlanLevel.value === 'free'
}

function goToCheckout(planLevel: string) {
  router.push({ name: 'checkout', query: { plan: planLevel } })
}

function formatAmount(amount: number): string {
  return `¥${amount.toFixed(2)}`
}

function formatProvider(provider: string | null): string {
  if (!provider) return '-'
  if (provider === 'wechat') return t('pricing.currentSubscription.wechat')
  if (provider === 'alipay') return t('pricing.currentSubscription.alipay')
  return provider
}

function formatOrderStatus(status: string): string {
  if (status === 'pending') return t('pricing.orderHistory.statusPending')
  if (status === 'paid') return t('pricing.orderHistory.statusPaid')
  if (status === 'cancelled') return t('pricing.orderHistory.statusCancelled')
  return status
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return dateStr
  }
}

onMounted(async () => {
  syncThemeMode()
  if (typeof MutationObserver !== 'undefined' && typeof document !== 'undefined') {
    themeObserver = new MutationObserver(syncThemeMode)
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
  }
  await loadQuota()
  if (isLoggedIn.value && !loadError.value) {
    await Promise.all([loadSubscription(), loadOrders(1), loadSimBots()])
  }
})

onBeforeUnmount(() => {
  themeObserver?.disconnect()
})
</script>

<style scoped>
/* ── View Root ── */
.pricing-view {
  width: 100%;
}

.pricing-page {
  padding-bottom: var(--spacing-xl);
}

/* ── Page Header — Bauhaus ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  position: relative;
  padding-bottom: var(--spacing-lg);
}

.page-header::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  height: 6px;
  background: var(--color-accent);
  border-radius: 3px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
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
  font-size: var(--font-size-xxxl);
  font-weight: 900;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  max-width: 480px;
  line-height: 1.6;
}

/* Bauhaus decorative shapes */
.header-deco {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.deco-circle {
  display: block;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  background: var(--color-accent);
  opacity: 0.15;
}

.deco-triangle {
  display: block;
  width: 0;
  height: 0;
  border-left: 18px solid transparent;
  border-right: 18px solid transparent;
  border-bottom: 30px solid var(--color-primary);
  opacity: 0.2;
}

/* ── Subscription Overview ── */
.sub-overview {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-xl);
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
}

.sub-overview__left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.sub-overview__badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 20px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xl);
  font-weight: 700;
  letter-spacing: 0.02em;
}

.sub-overview__badge--free {
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
  border: 2px solid var(--color-border);
}

.sub-overview__badge--go {
  background: rgba(54, 214, 182, 0.10);
  color: #1aab91;
  border: 2px solid rgba(54, 214, 182, 0.25);
}

.sub-overview__badge--plus {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  border: 2px solid var(--color-primary-border);
}

.sub-overview__badge--pro {
  background: rgba(240, 180, 41, 0.10);
  color: #c08e20;
  border: 2px solid rgba(240, 180, 41, 0.25);
}

.sub-overview__badge--ultra {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.12), rgba(218, 165, 32, 0.12));
  color: #c9a000;
  border: 2px solid rgba(255, 215, 0, 0.3);
}

.sub-overview__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-md);
}

.sub-overview__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-success);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.sub-overview__provider {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.sub-overview__right {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.sub-overview__usage-title {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.sub-overview__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.usage-stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 14px 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.usage-stat__label {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.usage-stat__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
  font-weight: 700;
  line-height: 1.2;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.usage-stat__meta {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.sub-overview__bar {
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-surface-active);
  overflow: hidden;
  border: 1px solid var(--color-border-light);
}

.sub-overview__bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
  transition: width var(--transition-fast);
}

/* ── Plus Recommendation — always blue border ── */

.plus-rec__icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  border: 2px solid var(--color-primary-border);
}

.plus-rec__text {
  flex: 1;
  min-width: 0;
}

.plus-rec__title {
  margin: 0 0 2px;
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

.plus-rec__desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ── Plus Recommendation — always blue border ── */
.plus-rec {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg) var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 1px var(--color-primary-border);
}

.plus-rec:hover {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 1px var(--color-primary-border), var(--shadow-md);
}

/* ── Pricing Grid ── */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-md);
  align-items: stretch;
}

/* ── Pricing Card — Bauhaus ── */
.pricing-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: 0;
  overflow: hidden;
  position: relative;
}

/* Top accent bar per plan */
.pricing-card__accent {
  height: 5px;
  width: 100%;
  flex-shrink: 0;
}

.pricing-card__accent--free {
  background: var(--color-text-muted);
}

.pricing-card__accent--go {
  background: #1aab91;
}

.pricing-card__accent--plus {
  background: var(--color-primary);
}

.pricing-card__accent--pro {
  background: var(--color-accent);
}

.pricing-card__accent--ultra {
  background: linear-gradient(90deg, #ffd700, #daa520, #ffd700);
}

.pricing-card--current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-border);
}

.pricing-card--lower-tier {
  opacity: 0.4;
}

.pricing-card--lower-tier:hover {
  transform: none;
  box-shadow: var(--shadow-md);
}

.pricing-card--featured {
  border-color: var(--color-primary);
  transform: scale(1.04);
  z-index: 2;
  box-shadow: var(--shadow-xl);
}

.pricing-card--featured:hover {
  transform: scale(1.04) translateY(-2px);
}

/* Ultra card — White Gold */
.pricing-card--ultra {
  border-color: #c9a000;
  background: linear-gradient(
    170deg,
    #fffdf6 0%,
    #fbf3d6 18%,
    #f6e7b8 40%,
    #efe1af 60%,
    #fbf3d6 80%,
    #fff7dc 100%
  );
  box-shadow:
    0 12px 36px -16px rgba(176, 131, 24, 0.35),
    0 0 0 1px rgba(218, 165, 32, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.pricing-card--ultra::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 25% 15%, rgba(255, 236, 128, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 75% 85%, rgba(255, 215, 0, 0.08) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

.pricing-card--ultra .pricing-card__name {
  color: #8a5c00;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.pricing-card--ultra .pricing-card__price,
.pricing-card--ultra .pricing-card__currency {
  background: linear-gradient(135deg, #b8860b 0%, #daa520 40%, #8a5c00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pricing-card--ultra .pricing-card__price {
  font-size: 2.2rem;
}

.pricing-card--ultra .pricing-card__quota {
  color: #8a6d10;
}

.pricing-card--ultra .pricing-card__capacity {
  color: rgba(120, 90, 20, 0.65);
}

.pricing-card--ultra .pricing-card__description {
  color: rgba(100, 75, 15, 0.7);
}

.pricing-card--ultra .pricing-card__divider {
  background: linear-gradient(90deg, transparent, rgba(218, 165, 32, 0.35), transparent);
  height: 1px;
  border: none;
}

.pricing-card--ultra .feature-icon--check {
  color: #b8860b;
}

.pricing-card--ultra .feature-text {
  color: rgba(80, 60, 10, 0.82);
}

.pricing-card--ultra .feature-item--disabled .feature-text {
  color: rgba(125, 102, 43, 0.4);
}

.pricing-card--ultra .feature-icon--cross {
  color: rgba(125, 102, 43, 0.25);
}

.pricing-card--ultra .btn-upgrade,
.pricing-card--ultra .btn-accent {
  background: linear-gradient(135deg, #ffd700 0%, #f0c850 50%, #daa520 100%);
  border-color: transparent;
  color: #3d2e00;
  font-weight: 700;
  box-shadow: 0 2px 12px -2px rgba(218, 165, 32, 0.35);
}

.pricing-card--ultra .btn-accent:hover {
  box-shadow: 0 4px 24px -4px rgba(218, 165, 32, 0.5);
  opacity: 0.9;
}

/* Inner content area */
.pricing-card__badges,
.pricing-card__header,
.pricing-card__quota-stack,
.pricing-card__description,
.pricing-card__actions,
.pricing-card__divider,
.feature-list {
  padding-left: var(--spacing-lg);
  padding-right: var(--spacing-lg);
}

.pricing-card__badges {
  padding-top: var(--spacing-md);
  display: flex;
  gap: var(--spacing-xs);
  min-height: 22px;
  position: relative;
  z-index: 2;
}

/* Badges */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  line-height: 1.6;
}

.badge--featured {
  background: var(--color-primary);
  color: #fff;
  border: 2px solid transparent;
}

.badge--current {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  border: 2px solid var(--color-primary-border);
}

.badge--ultra-vip {
  background: linear-gradient(135deg, rgba(218, 165, 32, 0.12), rgba(255, 215, 0, 0.10));
  color: #8a5c00;
  border: 2px solid rgba(218, 165, 32, 0.35);
  letter-spacing: 0.08em;
}

/* Header */
.pricing-card__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 2;
}

.pricing-card__name {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.02em;
}

.pricing-card__price-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.pricing-card__currency {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
  align-self: flex-start;
  margin-top: 5px;
  font-family: var(--font-mono);
}

.pricing-card__price {
  color: var(--color-text-primary);
  font-size: 2rem;
  font-weight: 900;
  line-height: 1;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.pricing-card__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin-left: 3px;
}

.pricing-card__promo-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: var(--color-danger);
  color: #fff;
  font-size: var(--font-size-xs);
  font-weight: 700;
  width: fit-content;
}

.pricing-card__original-price {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-decoration: line-through;
  margin-left: 6px;
  opacity: 0.6;
  font-family: var(--font-mono);
}

.pricing-card__quota-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  z-index: 2;
}

.pricing-card__quota {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
  font-family: 'KaiTi', '楷体', 'STKaiti', serif;
  font-variant-numeric: tabular-nums;
}

.pricing-card__capacity {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.02em;
}

/* Description */
.pricing-card__description {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.55;
  min-height: 36px;
  position: relative;
  z-index: 2;
}

/* CTA */
.pricing-card__actions {
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 2;
}

.btn-disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 500;
  border: 2px solid var(--color-border);
  cursor: default;
}

.btn-disabled--current {
  color: var(--color-primary);
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

/* Divider */
.pricing-card__divider {
  height: 1px;
  background: var(--color-border-light);
  border: none;
  margin: 0;
}

/* Features */
.feature-list {
  list-style: none;
  margin: 0;
  padding-bottom: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: 9px;
  position: relative;
  z-index: 2;
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.feature-icon svg { width: 16px; height: 16px; }
.feature-icon--check { color: var(--color-success); }
.feature-icon--cross { color: var(--color-text-muted); }

.feature-text {
  font-size: var(--font-size-sm);
  line-height: 1.4;
  color: var(--color-text-secondary);
}

.feature-item--disabled .feature-text {
  color: var(--color-text-muted);
}

/* ── Trust Strip ── */
.pricing-trust {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-lg) 0;
  border-top: 2px solid var(--color-border);
}

.pricing-trust__item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

/* ── Orders ── */
.pricing-orders {
  margin-top: var(--spacing-xl);
  padding: 0;
  overflow: hidden;
}

.orders-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.panel-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  flex-shrink: 0;
}

.orders-header__title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
}

.orders-table-wrap {
  overflow-x: auto;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.orders-table th {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  color: var(--color-text-muted);
  font-weight: 700;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface);
}

.orders-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border-light);
}

.orders-table tbody tr:last-child td {
  border-bottom: none;
}

.order-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  border: 1px solid transparent;
}

.order-status--paid {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: rgba(46, 125, 50, 0.2);
}

.order-status--pending {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border-color: rgba(230, 81, 0, 0.2);
}

.order-status--cancelled {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border-color: rgba(212, 57, 59, 0.2);
}

/* Pagination */
.orders-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.orders-pagination__indicator {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
}

.btn--sm {
  padding: 5px 12px;
  font-size: var(--font-size-xs);
}

/* Ghost button */
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  font-family: inherit;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.btn-ghost:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Panel empty */
.panel-empty {
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── Messages ── */
.message {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-muted);
  text-align: center;
}

.message.error {
  color: var(--color-danger);
}

/* ── Responsive ── */
@media (max-width: 1400px) {
  .pricing-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .pricing-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pricing-trust { flex-wrap: wrap; gap: var(--spacing-md); }
  .sub-overview { grid-template-columns: 1fr; }
  .sub-overview__stats { grid-template-columns: 1fr; }
  .plus-rec { flex-direction: column; text-align: center; }
  .header-deco { display: none; }
  .orders-table { font-size: 12px; }
  .orders-table th,
  .orders-table td { padding: var(--spacing-xs) var(--spacing-sm); }
}

@media (max-width: 560px) {
  .page-header {
    flex-direction: column;
  }
  .pricing-grid { grid-template-columns: 1fr; }
  .pricing-trust { flex-direction: column; align-items: flex-start; }
  .pricing-card--featured { transform: none; }
  .pricing-card--featured:hover { transform: translateY(-2px); }
}
</style>
