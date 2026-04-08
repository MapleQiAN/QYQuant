<template>
  <section class="view pricing-view">
    <div class="container pricing-page">
      <header class="pricing-hero">
        <h1 class="pricing-hero__title">选择适合你的回测套餐</h1>
        <p class="pricing-hero__subtitle">按月解锁更多回测次数和更多高级功能，助力你的量化研究之路。</p>
      </header>

      <p v-if="loading" class="message">正在加载套餐信息...</p>
      <template v-else>
        <p v-if="!isLoggedIn" class="message login-hint">请先登录以查看当前套餐信息并进行升级。</p>
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
            <span v-if="plan.featured && shouldShowFeatured" class="badge badge--featured">推荐</span>
            <span v-if="currentPlanLevel === plan.level" class="badge badge--current">当前套餐</span>
          </div>

          <!-- Plan name & price -->
          <div class="pricing-card__header">
            <p class="pricing-card__name">{{ plan.name }}</p>
            <div v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__promo-tag">新用户首充</div>
            <div class="pricing-card__price-row">
              <span class="pricing-card__currency">¥</span>
              <span class="pricing-card__price tnum">{{ firstPurchaseEligible && plan.promoPrice != null ? plan.promoPrice : plan.price }}</span>
              <span class="pricing-card__unit">/ 月</span>
              <span v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__original-price tnum">¥{{ plan.price }}</span>
            </div>
          </div>

          <!-- Quota -->
          <div class="pricing-card__quota">
            {{ plan.quota === null ? '无限回测次数' : `${plan.quota} 次 / 月` }}
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
              升级到 {{ plan.name }}
            </button>
            <div v-else-if="plan.level === 'free' && isPlanTierLowerThanCurrent(plan.level)" class="btn btn-disabled" aria-disabled="true">
              您已拥有{{ currentPlanName }}套餐
            </div>
            <div v-else-if="plan.level !== 'free' && currentPlanLevel !== plan.level && isPlanTierLowerThanCurrent(plan.level)" class="btn btn-disabled" aria-disabled="true">
              您已拥有{{ currentPlanName }}套餐
            </div>
            <div v-else-if="plan.level === 'free'" class="btn btn-disabled" aria-disabled="true">
              免费体验套餐
            </div>
            <div v-else class="btn btn-disabled btn-disabled--current" aria-disabled="true">
              你当前的套餐
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
          <span>安全支付</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>数据加密</span>
        </div>
        <div class="pricing-trust__item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
          </svg>
          <span>随时升降级</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { PlanLevel } from '../api/payments'
import { fetchMyQuota } from '../api/users'
import { PLANS, PLAN_TIER_ORDER } from '../data/plans'

const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const isLoggedIn = ref(false)
const currentPlanLevel = ref<PlanLevel>('free')
const firstPurchaseEligible = ref(true)

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
    const quota = await fetchMyQuota()
    currentPlanLevel.value = quota.plan_level as PlanLevel
    firstPurchaseEligible.value = quota.first_purchase_eligible
  } catch (error: any) {
    loadError.value = error?.message || '套餐信息加载失败'
  } finally {
    loading.value = false
  }
}

const currentPlanName = computed(() => {
  return PLANS.find(p => p.level === currentPlanLevel.value)?.name ?? ''
})

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

onMounted(() => {
  void loadQuota()
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
}

@media (max-width: 560px) {
  .pricing-hero { text-align: left; }
  .pricing-grid { grid-template-columns: 1fr; }
  .pricing-trust { flex-direction: column; align-items: flex-start; }
}
</style>
