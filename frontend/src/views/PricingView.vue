<template>
  <section class="view pricing-view">
    <div class="container pricing-page">
      <header class="pricing-hero">
        <h1 class="pricing-hero__title">{{ t('pages.pricingTitle') }}</h1>
        <p class="pricing-hero__subtitle">{{ t('pages.pricingDescription') }}</p>
      </header>

      <p v-if="loading" class="message">{{ t('pricing.loadingPlans') }}</p>
      <template v-else>
        <p v-if="!isLoggedIn" class="message login-hint">{{ t('pricing.loginHint') }}</p>
        <p v-else-if="loadError" class="message error">{{ loadError }}</p>
      </template>

      <div v-if="!loading && (isLoggedIn ? !loadError : true)" class="pricing-grid">
        <article
          v-for="plan in PLANS"
          :key="plan.level"
          class="pricing-card"
          :class="{
            'pricing-card--current': currentPlanLevel === plan.level,
            'pricing-card--lower-tier': isLoggedIn && isPlanTierLowerThanCurrent(plan.level) && currentPlanLevel !== plan.level,
            'pricing-card--featured': plan.featured && shouldShowFeatured,
          }"
        >
          <!-- Badge row -->
          <div class="pricing-card__badges">
            <span v-if="plan.featured && shouldShowFeatured" class="badge badge--featured">{{ t('pricing.featured') }}</span>
            <span v-if="currentPlanLevel === plan.level" class="badge badge--current">{{ t('pricing.currentPlan') }}</span>
          </div>

          <!-- Plan name & price -->
          <div class="pricing-card__header">
            <p class="pricing-card__name">{{ plan.name }}</p>
            <div v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__promo-tag">{{ t('pricing.promoTag') }}</div>
            <div class="pricing-card__price-row">
              <span class="pricing-card__currency">&yen;</span>
              <span class="pricing-card__price tnum">{{ firstPurchaseEligible && plan.promoPrice != null ? plan.promoPrice : plan.price }}</span>
              <span class="pricing-card__unit">{{ t('common.perMonthUnit') }}</span>
              <span v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__original-price tnum">&yen;{{ plan.price }}</span>
            </div>
          </div>

          <!-- Quota -->
          <div class="pricing-card__quota">
            {{ plan.quota === null ? t('pricing.unlimitedBacktests') : t('pricing.backtestsPerMonth', { quota: plan.quota }) }}
          </div>

          <p class="pricing-card__description">{{ plan.description }}</p>

          <!-- CTA -->
          <div class="pricing-card__actions">
            <button
              v-if="plan.level !== 'free' && currentPlanLevel !== plan.level && !isPlanTierLowerThanCurrent(plan.level)"
              class="btn btn-upgrade"
              :class="{ 'btn-upgrade--featured': plan.featured && shouldShowFeatured }"
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

          <!-- Features list -->
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

      <!-- Bottom trust strip -->
      <div class="pricing-trust">
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <span>{{ t('pricing.trustSecure') }}</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>{{ t('pricing.trustEncrypted') }}</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
          </svg>
          <span>{{ t('pricing.trustFlexible') }}</span>
        </div>
      </div>

      <!-- Logged-in panels -->
      <template v-if="isLoggedIn && !loading">
        <div class="pricing-panels">
          <!-- Usage details panel -->
          <div class="pricing-panel">
            <h3 class="pricing-panel__title">{{ t('pricing.usageDetails.title') }}</h3>
            <div v-if="quota" class="usage-stats">
              <div class="usage-stats__numbers">
                <span class="usage-stats__used">{{ quota.used_count }}</span>
                <span class="usage-stats__separator">/</span>
                <span class="usage-stats__total">{{ quota.plan_limit === 'unlimited' ? t('pricing.usageDetails.unlimited') : quota.plan_limit }}</span>
              </div>
              <div v-if="quota.plan_limit !== 'unlimited'" class="usage-bar">
                <div class="usage-bar__fill" :style="{ width: usagePercentage + '%' }" />
              </div>
              <p class="usage-stats__remaining">
                {{ t('pricing.usageDetails.remaining') }}:
                {{ quota.remaining === 'unlimited' ? t('pricing.usageDetails.unlimited') : quota.remaining }}
              </p>
            </div>
            <p v-else class="panel-empty">{{ t('common.noData') }}</p>
          </div>

          <!-- Current subscription panel -->
          <div class="pricing-panel">
            <h3 class="pricing-panel__title">{{ t('pricing.currentSubscription.title') }}</h3>
            <div v-if="subscription" class="sub-details">
              <div class="sub-detail">
                <span class="sub-detail__label">{{ t('pricing.currentSubscription.plan') }}</span>
                <span class="sub-detail__value">{{ subscriptionPlanName }}</span>
              </div>
              <div class="sub-detail">
                <span class="sub-detail__label">{{ t('pricing.currentSubscription.status') }}</span>
                <span class="sub-detail__value sub-detail__value--active">{{ t('pricing.currentSubscription.activeStatus') }}</span>
              </div>
              <div class="sub-detail">
                <span class="sub-detail__label">{{ t('pricing.currentSubscription.paymentMethod') }}</span>
                <span class="sub-detail__value">{{ formatProvider(subscription.payment_provider) }}</span>
              </div>
              <div v-if="subscription.ends_at" class="sub-detail">
                <span class="sub-detail__label">{{ t('pricing.currentSubscription.expiresAt') }}</span>
                <span class="sub-detail__value">{{ formatDate(subscription.ends_at) }}</span>
              </div>
            </div>
            <p v-else class="panel-empty">{{ t('pricing.currentSubscription.noActive') }}</p>
          </div>
        </div>

        <!-- Order history -->
        <div class="pricing-orders">
          <h3 class="pricing-orders__title">{{ t('pricing.orderHistory.title') }}</h3>
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
                class="btn-page"
                :disabled="ordersCurrentPage <= 1"
                type="button"
                @click="loadOrders(ordersCurrentPage - 1)"
              >
                {{ t('pricing.orderHistory.previousPage') }}
              </button>
              <span class="orders-pagination__indicator">
                {{ t('pricing.orderHistory.pageIndicator', { current: ordersCurrentPage, total: totalPages }) }}
              </span>
              <button
                class="btn-page"
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
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { OrderItem, PlanLevel, SubscriptionResponse } from '../api/payments'
import { fetchMyOrders, fetchMySubscription } from '../api/payments'
import type { UserQuotaResponse } from '../api/users'
import { fetchMyQuota } from '../api/users'
import { PLANS, PLAN_TIER_ORDER } from '../data/plans'

const { t } = useI18n()
const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const isLoggedIn = ref(false)
const currentPlanLevel = ref<PlanLevel>('free')
const firstPurchaseEligible = ref(true)
const quota = ref<UserQuotaResponse | null>(null)
const subscription = ref<SubscriptionResponse | null>(null)
const orders = ref<OrderItem[]>([])
const ordersCurrentPage = ref(1)
const ordersTotal = ref(0)
const ordersPerPage = ref(10)

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

const usagePercentage = computed(() => {
  if (!quota.value || quota.value.plan_limit === 'unlimited') return 0
  const limit = quota.value.plan_limit as number
  if (limit === 0) return 0
  return Math.min(Math.round((quota.value.used_count / limit) * 100), 100)
})

const subscriptionPlanName = computed(() => {
  if (!subscription.value) return ''
  return PLANS.find(p => p.level === subscription.value!.plan_level)?.name ?? subscription.value.plan_level
})

const totalPages = computed(() => Math.max(1, Math.ceil(ordersTotal.value / ordersPerPage.value)))

function getPlanName(planLevel: string): string {
  return PLANS.find(p => p.level === planLevel)?.name ?? planLevel
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
  await loadQuota()
  if (isLoggedIn.value && !loadError.value) {
    await Promise.all([loadSubscription(), loadOrders(1)])
  }
})
</script>

<style scoped>
.pricing-view {
  width: 100%;
}

.pricing-page {
  padding-bottom: var(--spacing-xl);
}

/* Hero */
.pricing-hero {
  margin-bottom: var(--spacing-xl);
  text-align: center;
  padding-top: var(--spacing-md);
}

.pricing-hero__title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  line-height: 1.2;
}

.pricing-hero__subtitle {
  margin: 0 auto;
  max-width: 480px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
  line-height: 1.6;
}

/* Grid */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-md);
  align-items: start;
}

/* Card */
.pricing-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.pricing-card--current {
  border-color: var(--color-primary-border);
}

.pricing-card--lower-tier {
  opacity: 0.55;
}

.pricing-card--featured {
  border-color: var(--color-primary);
}

/* Badges */
.pricing-card__badges {
  display: flex;
  gap: var(--spacing-xs);
  min-height: 22px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
  line-height: 1.6;
}

.badge--featured {
  background: var(--color-primary);
  color: #fff;
}

.badge--current {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

/* Header */
.pricing-card__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pricing-card__name {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.pricing-card__price-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.pricing-card__currency {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 600;
  align-self: flex-start;
  margin-top: 5px;
}

.pricing-card__price {
  color: var(--color-text-primary);
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
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
  font-size: 11px;
  font-weight: 600;
  width: fit-content;
}

.pricing-card__original-price {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-decoration: line-through;
  margin-left: 6px;
  opacity: 0.7;
}

/* Quota */
.pricing-card__quota {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

/* Description */
.pricing-card__description {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.55;
  min-height: 36px;
}

/* CTA */
.pricing-card__actions {
  display: flex;
  flex-direction: column;
}

.btn-upgrade {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.btn-upgrade:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-hover);
}

.btn-upgrade--featured {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.btn-upgrade--featured:hover {
  opacity: 0.9;
  background: var(--color-primary);
  border-color: var(--color-primary);
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
  border: 1px solid var(--color-border);
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
  background: var(--color-border);
}

/* Features */
.feature-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
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

/* Trust strip */
.pricing-trust {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--color-border);
}

.pricing-trust__item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.pricing-trust__item svg {
  color: var(--color-text-muted);
}

/* Panels (usage + subscription) */
.pricing-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.pricing-panel {
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.pricing-panel__title {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.panel-empty {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* Usage stats */
.usage-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.usage-stats__numbers {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.usage-stats__used {
  color: var(--color-text-primary);
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
}

.usage-stats__separator {
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
}

.usage-stats__total {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
}

.usage-bar {
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-border);
  overflow: hidden;
}

.usage-bar__fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  transition: width var(--transition-fast);
}

.usage-stats__remaining {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* Subscription details */
.sub-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.sub-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sub-detail__label {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.sub-detail__value {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.sub-detail__value--active {
  color: var(--color-success);
}

/* Orders */
.pricing-orders {
  margin-top: var(--spacing-xl);
}

.pricing-orders__title {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.orders-table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
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
  font-weight: 500;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.orders-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.orders-table tbody tr:last-child td {
  border-bottom: none;
}

.order-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.order-status--paid {
  background: var(--color-primary-bg);
  color: var(--color-success);
}

.order-status--pending {
  background: var(--color-warning-bg, #fef3c7);
  color: var(--color-warning, #d97706);
}

.order-status--cancelled {
  background: var(--color-danger-bg, #fef2f2);
  color: var(--color-danger);
}

/* Pagination */
.orders-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.orders-pagination__indicator {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.btn-page {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.btn-page:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-border-hover);
}

.btn-page:disabled {
  opacity: 0.4;
  cursor: default;
}

/* Messages */
.message {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-muted);
  text-align: center;
}

.message.error {
  color: var(--color-danger);
}

/* Responsive */
@media (max-width: 1400px) {
  .pricing-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .pricing-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pricing-trust { flex-wrap: wrap; gap: var(--spacing-md); }
  .pricing-panels { grid-template-columns: 1fr; }
  .orders-table { font-size: 12px; }
  .orders-table th,
  .orders-table td { padding: var(--spacing-xs) var(--spacing-sm); }
}

@media (max-width: 560px) {
  .pricing-hero { text-align: left; }
  .pricing-grid { grid-template-columns: 1fr; }
  .pricing-trust { flex-direction: column; align-items: flex-start; }
}
</style>
