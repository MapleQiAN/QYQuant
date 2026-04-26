<template>
  <section class="view">
    <div class="container checkout-page">
      <!-- Back -->
      <button class="back-btn" type="button" @click="router.push({ name: 'pricing' })">
        <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('checkout.backToPlans') }}
      </button>

      <!-- Unknown plan guard -->
      <div v-if="!plan" class="unknown-plan">
        <p class="unknown-plan__text">{{ t('checkout.unknownPlan') }}</p>
        <button class="btn btn-primary" type="button" @click="router.push({ name: 'pricing' })">
          {{ t('checkout.backToPlans') }}
        </button>
      </div>

      <template v-else>
        <div class="checkout-layout">
          <!-- ── Left: Plan summary ── -->
          <aside class="plan-summary">
            <div class="plan-summary__badge" v-if="plan.featured && shouldShowFeatured">{{ t('checkout.featuredPlan') }}</div>

            <div class="plan-summary__header">
              <p class="plan-summary__label">{{ plan.name }}</p>
              <div v-if="shouldShowPromoPrice" class="plan-summary__promo-tag">{{ t('checkout.firstPurchasePromo') }}</div>
              <div class="plan-summary__price-row">
                <span class="plan-summary__currency">¥</span>
                <span class="plan-summary__price">{{ displayPrice }}</span>
                <span class="plan-summary__unit">{{ t('common.perMonthUnit') }}</span>
                <span v-if="shouldShowPromoPrice" class="plan-summary__original-price">¥{{ plan.price }}</span>
              </div>
            </div>

            <p class="plan-summary__description">{{ plan.description }}</p>

            <div class="plan-summary__quota">
              <svg viewBox="0 0 16 16" fill="none" class="quota-icon" aria-hidden="true">
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.25"/>
                <path d="M8 5v3.5l2 1" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/>
              </svg>
              {{ planQuotaLabel }}
            </div>

            <div class="plan-summary__divider" aria-hidden="true"></div>

            <ul class="plan-summary__features" role="list">
              <li
                v-for="feature in plan.features"
                :key="feature.text"
                class="feature-item"
                :class="{ 'feature-item--disabled': !feature.included }"
              >
                <span v-if="feature.included" class="feature-icon feature-icon--check" aria-hidden="true">
                  <svg viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="7" fill="currentColor" opacity="0.15"/>
                    <path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
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
          </aside>

          <!-- ── Right: Payment section ── -->
          <main class="payment-section">
            <h1 class="payment-section__title">{{ t('checkout.selectPaymentMethod') }}</h1>
            <p class="payment-section__subtitle">
              {{ t('checkout.upgradePrefix') }}
              <strong>{{ plan.name }}</strong>
              {{ t('checkout.upgradeSuffix', { price: displayPrice }) }}
            </p>

            <div v-if="!isLoggedIn" class="auth-hint">
              <svg viewBox="0 0 20 20" fill="currentColor" class="auth-hint__icon" aria-hidden="true">
                <path fill-rule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM9 9a1 1 0 0 0 0 2v3a1 1 0 0 0 1 1h1a1 1 0 1 0 0-2v-3a1 1 0 0 0-1-1H9z" clip-rule="evenodd"/>
              </svg>
              {{ t('checkout.loginRequired') }}
            </div>

            <!-- Payment method cards -->
            <div v-else class="payment-methods">
              <!-- WeChat Pay -->
              <button
                class="payment-method-card"
                type="button"
                :disabled="submitting"
                @click="handlePay('wechat')"
              >
                <div class="payment-method-card__logo payment-method-card__logo--wechat">
                  <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
                    <rect width="40" height="40" rx="10" fill="#07C160"/>
                    <path d="M15 18.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z" fill="#fff"/>
                    <path fill-rule="evenodd" d="M8 15.75C8 11.474 13.373 8 20 8s12 3.474 12 7.75c0 4.277-5.373 7.75-12 7.75a14.7 14.7 0 0 1-3.015-.312l-3.213 2.143a.5.5 0 0 1-.77-.427l.17-3.03A7.5 7.5 0 0 1 8 15.75z" fill="#fff" opacity="0.9"/>
                    <path d="M22 25.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm4.5 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2z" fill="#07C160"/>
                    <path fill-rule="evenodd" d="M19 23c0-2.761 3.134-5 7-5s7 2.239 7 5-3.134 5-7 5a9.4 9.4 0 0 1-1.9-.194l-2.017 1.347a.5.5 0 0 1-.77-.427l.105-1.875A4.8 4.8 0 0 1 19 23z" fill="#07C160" opacity="0.85"/>
                  </svg>
                </div>
                <div class="payment-method-card__info">
                  <p class="payment-method-card__name">{{ t('checkout.wechatPay') }}</p>
                  <p class="payment-method-card__desc">{{ t('checkout.wechatPayDescription') }}</p>
                </div>
                <svg class="payment-method-card__arrow" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>

              <!-- Alipay -->
              <button
                class="payment-method-card"
                type="button"
                :disabled="submitting"
                @click="handlePay('alipay')"
              >
                <div class="payment-method-card__logo payment-method-card__logo--alipay">
                  <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
                    <rect width="40" height="40" rx="10" fill="#1677FF"/>
                    <path d="M20 10c-5.523 0-10 4.477-10 10s4.477 10 10 10 10-4.477 10-10S25.523 10 20 10z" fill="#fff" opacity="0.15"/>
                    <text x="20" y="25" text-anchor="middle" fill="#fff" font-size="16" font-weight="bold" font-family="Arial">支</text>
                  </svg>
                </div>
                <div class="payment-method-card__info">
                  <p class="payment-method-card__name">{{ t('checkout.alipay') }}</p>
                  <p class="payment-method-card__desc">{{ t('checkout.alipayDescription') }}</p>
                </div>
                <svg class="payment-method-card__arrow" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <!-- Loading overlay -->
            <div v-if="submitting" class="processing-hint" role="status" aria-live="polite">
              <span class="spinner" aria-hidden="true"></span>
              {{ t('checkout.createOrderPending') }}
            </div>

            <!-- Error -->
            <p v-if="actionError" class="action-error" role="alert">{{ actionError }}</p>

            <!-- WeChat QR modal -->
            <div v-if="wechatPayUrl" class="qr-overlay" role="dialog" aria-modal="true" :aria-label="t('checkout.wechatPayQrCode')">
              <div class="qr-card">
                <button class="qr-card__close" type="button" :aria-label="t('common.close')" @click="wechatPayUrl = ''">
                  <svg viewBox="0 0 16 16" fill="none">
                    <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </button>
                <div class="qr-card__logo">
                  <svg viewBox="0 0 24 24" fill="none" class="qr-wechat-icon" aria-hidden="true">
                    <path fill-rule="evenodd" d="M4.5 9a7.5 7.5 0 1 1 15 0c0 4.142-3.358 7.5-7.5 7.5a8 8 0 0 1-2.046-.265l-2.165 1.444a.5.5 0 0 1-.77-.427l.144-2.574A7.5 7.5 0 0 1 4.5 9z" fill="#07C160"/>
                  </svg>
                </div>
                <h2 class="qr-card__title">{{ t('checkout.wechatPayQrCode') }}</h2>
                <p class="qr-card__amount">¥{{ displayPrice }} {{ t('common.perMonthUnit') }}</p>
                <img class="qr-card__img" :src="wechatPayUrl" :alt="t('checkout.wechatPayQrCode')" />
                <a class="qr-card__link" :href="wechatPayUrl" target="_blank" rel="noopener">
                  {{ t('checkout.openPaymentLink') }}
                </a>
                <p class="qr-card__hint">{{ t('checkout.autoActivateHint') }}</p>
              </div>
            </div>
          </main>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { createPaymentOrder, type PaymentProvider } from '../api/payments'
import { fetchMyQuota } from '../api/users'
import { buildPlans, PLAN_TIER_ORDER } from '../data/plans'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const plans = computed(() => buildPlans(t))
const planLevel = computed(() => (route.query.plan as string) || '')
const plan = computed(() => plans.value.find((p) => p.level === planLevel.value) ?? null)

const isLoggedIn = computed(() => !!localStorage.getItem('qyquant-token'))
const firstPurchaseEligible = ref(true)
const currentPlanLevel = ref('free')

const shouldShowFeatured = computed(() => {
  const currentTier = PLAN_TIER_ORDER[currentPlanLevel.value] ?? 0
  return currentTier < PLAN_TIER_ORDER['plus']
})

const shouldShowPromoPrice = computed(() => {
  if (!plan.value || plan.value.promoPrice == null) return false
  if (!isLoggedIn.value) return true
  return firstPurchaseEligible.value && currentPlanLevel.value === 'free'
})

const displayPrice = computed(() => {
  if (!plan.value) return 0
  return shouldShowPromoPrice.value
    ? plan.value.promoPrice
    : plan.value.price
})

const planQuotaLabel = computed(() => {
  if (!plan.value) return ''
  return plan.value.quota === null
    ? t('pricing.unlimitedBacktests')
    : t('pricing.backtestsPerMonth', { quota: plan.value.quota })
})

onMounted(async () => {
  if (isLoggedIn.value) {
    try {
      const quota = await fetchMyQuota()
      firstPurchaseEligible.value = quota.first_purchase_eligible
      currentPlanLevel.value = quota.plan_level
    } catch {
      // 查询失败则保持默认展示优惠价，后端下单时会再次校验
    }
  }
})

const submitting = ref(false)
const actionError = ref('')
const wechatPayUrl = ref('')

async function handlePay(provider: PaymentProvider) {
  if (!isLoggedIn.value) return
  actionError.value = ''
  submitting.value = true
  wechatPayUrl.value = ''

  try {
    const order = await createPaymentOrder({
      plan_level: planLevel.value as any,
      provider,
    })

    if (provider === 'alipay') {
      window.open(order.pay_url, '_blank', 'noopener')
    } else {
      wechatPayUrl.value = order.pay_url
    }
  } catch (error: any) {
    actionError.value = error?.message || t('checkout.createOrderFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* ── Page ── */
.view {
  width: 100%;
}

.checkout-page {
  padding-bottom: var(--spacing-xl);
}

/* ── Back ── */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: var(--spacing-lg);
  padding: 6px 12px 6px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: color 150ms ease, border-color 150ms ease, background 150ms ease;
}

.back-btn svg {
  width: 16px;
  height: 16px;
}

.back-btn:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border-hover);
  background: var(--color-surface-hover);
}

/* ── Unknown plan ── */
.unknown-plan {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xxl) 0;
  text-align: center;
}

.unknown-plan__text {
  margin: 0;
  color: var(--color-text-muted);
}

/* ── Layout ── */
.checkout-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: var(--spacing-xl);
  align-items: start;
}

/* ── Plan Summary (left) ── */
.plan-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-xl);
  background: linear-gradient(160deg, var(--color-primary-bg) 0%, var(--color-surface) 55%);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--color-primary);
  position: sticky;
  top: calc(var(--nav-height, 48px) + var(--spacing-md));
}

.plan-summary__badge {
  display: inline-flex;
  align-self: flex-start;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.plan-summary__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-summary__label {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.plan-summary__price-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.plan-summary__currency {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  align-self: flex-start;
  margin-top: 5px;
}

.plan-summary__price {
  color: var(--color-text-primary);
  font-size: 2.4rem;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.plan-summary__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin-left: 3px;
}

.plan-summary__promo-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7a45 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  width: fit-content;
}

.plan-summary__original-price {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-decoration: line-through;
  margin-left: 6px;
  opacity: 0.7;
}

.plan-summary__description {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.55;
}

.plan-summary__quota {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.quota-icon {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

.plan-summary__divider {
  height: 1px;
  background: var(--color-border);
}

.plan-summary__features {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

/* ── Payment Section (right) ── */
.payment-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.payment-section__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
}

.payment-section__subtitle {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.payment-section__subtitle strong {
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-semibold);
}

/* ── Auth hint ── */
.auth-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: var(--font-size-sm);
}

.auth-hint__icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* ── Payment method cards ── */
.payment-methods {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.payment-method-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  cursor: pointer;
  text-align: left;
  transition: border-color 150ms ease, background 150ms ease, box-shadow 150ms ease, transform 150ms ease;
}

.payment-method-card:hover:not(:disabled) {
  border-color: var(--color-primary-border);
  background: var(--color-surface-hover);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.payment-method-card:active:not(:disabled) {
  transform: translateY(0);
}

.payment-method-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.payment-method-card__logo {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}

.payment-method-card__logo svg {
  width: 40px;
  height: 40px;
}

.payment-method-card__info {
  flex: 1;
  min-width: 0;
}

.payment-method-card__name {
  margin: 0 0 2px;
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.payment-method-card__desc {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.payment-method-card__arrow {
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
  flex-shrink: 0;
  transition: color 150ms ease, transform 150ms ease;
}

.payment-method-card:hover:not(:disabled) .payment-method-card__arrow {
  color: var(--color-primary);
  transform: translateX(2px);
}

/* ── Processing ── */
.processing-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border-strong);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Error ── */
.action-error {
  margin: 0;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

/* ── WeChat QR ── */
.qr-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: var(--color-overlay, rgba(0, 0, 0, 0.6));
  z-index: 100;
}

.qr-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  width: min(360px, 100%);
  padding: var(--spacing-xl) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-xl);
  text-align: center;
}

.qr-card__close {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease;
}

.qr-card__close:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.qr-card__close svg {
  width: 14px;
  height: 14px;
}

.qr-wechat-icon {
  width: 36px;
  height: 36px;
}

.qr-card__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
}

.qr-card__amount {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.qr-card__img {
  display: block;
  width: min(200px, 100%);
  border-radius: var(--radius-md);
  background: var(--color-surface-hover);
}

.qr-card__link {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  text-decoration: none;
}

.qr-card__link:hover {
  text-decoration: underline;
}

.qr-card__hint {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.5;
}

/* ── Shared feature list styles ── */
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

.feature-icon svg {
  width: 16px;
  height: 16px;
}

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

/* ── Responsive ── */
@media (max-width: 900px) {
  .checkout-layout {
    grid-template-columns: 1fr;
  }

  .plan-summary {
    position: static;
  }
}
</style>
