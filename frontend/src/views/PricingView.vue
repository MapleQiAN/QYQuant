<template>
  <section class="view">
    <div class="container pricing-page">
      <header class="pricing-hero">
        <p class="pricing-eyebrow">套餐升级</p>
        <h1 class="view-title">选择适合你的回测套餐</h1>
        <p class="view-subtitle">按月解锁更多回测次数，支持微信支付和支付宝。</p>
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
            'pricing-card--featured': plan.featured,
          }"
        >
          <!-- Badge row -->
          <div class="pricing-card__badges">
            <span v-if="plan.featured" class="badge badge--featured">推荐</span>
            <span v-if="currentPlanLevel === plan.level" class="badge badge--current">当前套餐</span>
          </div>

          <!-- Plan name & price -->
          <div class="pricing-card__header">
            <p class="pricing-card__name">{{ plan.name }}</p>
            <div class="pricing-card__price-row">
              <span class="pricing-card__currency">¥</span>
              <span class="pricing-card__price">{{ plan.price }}</span>
              <span class="pricing-card__unit">/ 月</span>
            </div>
          </div>

          <!-- Quota highlight -->
          <div class="pricing-card__quota-row">
            <svg class="quota-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.25"/>
              <path d="M8 5v3.5l2 1" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/>
            </svg>
            <span class="pricing-card__quota">
              {{ plan.quota === null ? '无限回测次数' : `${plan.quota} 次 / 月` }}
            </span>
          </div>

          <p class="pricing-card__description">{{ plan.description }}</p>

          <!-- CTA -->
          <div class="pricing-card__actions">
            <button
              v-if="plan.level !== 'free' && currentPlanLevel !== plan.level"
              class="btn btn-upgrade"
              :class="{ 'btn-upgrade--featured': plan.featured }"
              type="button"
              @click="goToCheckout(plan.level)"
            >
              升级到 {{ plan.name }}
              <svg viewBox="0 0 16 16" fill="none" class="btn-arrow" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div v-else-if="plan.level === 'free'" class="btn btn-disabled" aria-disabled="true">
              免费体验套餐
            </div>
            <div v-else class="btn btn-disabled btn-disabled--current" aria-disabled="true">
              <svg viewBox="0 0 16 16" fill="none" class="btn-check-icon" aria-hidden="true">
                <path d="M3 8l3 3 7-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              你当前的套餐
            </div>
          </div>

          <!-- Divider -->
          <div class="pricing-card__divider" aria-hidden="true"></div>

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
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { PlanLevel } from '../api/payments'
import { fetchMyQuota } from '../api/users'
import { PLANS } from '../data/plans'

const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const isLoggedIn = ref(false)
const currentPlanLevel = ref<PlanLevel>('free')

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
  } catch (error: any) {
    loadError.value = error?.message || '套餐信息加载失败'
  } finally {
    loading.value = false
  }
}

function goToCheckout(planLevel: string) {
  router.push({ name: 'checkout', query: { plan: planLevel } })
}

onMounted(() => {
  void loadQuota()
})
</script>

<style scoped>
/* ── Page ── */
.view {
  width: 100%;
}

.pricing-page {
  padding-bottom: var(--spacing-xl);
}

.pricing-hero {
  margin-bottom: var(--spacing-xl);
  text-align: center;
}

.pricing-eyebrow {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
  font-size: var(--font-size-xxxl);
  font-weight: var(--font-weight-bold);
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
}

/* ── Grid ── */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-md);
  align-items: start;
}

/* ── Card ── */
.pricing-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 200ms ease, border-color 200ms ease, transform 200ms ease;
  position: relative;
}

.pricing-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
}

.pricing-card--current {
  border-color: var(--color-primary-border);
}

.pricing-card--featured {
  border-color: var(--color-primary);
  background: linear-gradient(160deg, var(--color-primary-bg) 0%, var(--color-surface) 55%);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--color-primary);
}

.pricing-card--featured:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg), 0 0 0 1px var(--color-primary);
}

/* ── Badges ── */
.pricing-card__badges {
  display: flex;
  gap: var(--spacing-xs);
  min-height: 22px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  line-height: 1.6;
}

.badge--featured {
  background: var(--color-primary);
  color: #fff;
}

.badge--current {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-border);
}

/* ── Header ── */
.pricing-card__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pricing-card__name {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.pricing-card__price-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.pricing-card__currency {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  align-self: flex-start;
  margin-top: 5px;
}

.pricing-card__price {
  color: var(--color-text-primary);
  font-size: 2.2rem;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.pricing-card__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin-left: 3px;
}

/* ── Quota ── */
.pricing-card__quota-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.quota-icon {
  width: 13px;
  height: 13px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.pricing-card__quota {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

/* ── Description ── */
.pricing-card__description {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.55;
  min-height: 36px;
}

/* ── CTA ── */
.pricing-card__actions {
  display: flex;
  flex-direction: column;
}

.btn-upgrade {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease, transform 150ms ease, box-shadow 150ms ease;
  white-space: nowrap;
}

.btn-upgrade:hover {
  background: var(--color-surface-active);
  border-color: var(--color-border-hover);
  transform: translateY(-1px);
}

.btn-upgrade:active {
  transform: translateY(0);
}

.btn-upgrade--featured {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.35);
}

.btn-upgrade--featured:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary-light);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.45);
}

.btn-arrow {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.btn-disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border: 1px solid var(--color-border);
  cursor: default;
  user-select: none;
}

.btn-disabled--current {
  color: var(--color-primary);
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.btn-check-icon {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

/* ── Divider ── */
.pricing-card__divider {
  height: 1px;
  background: var(--color-border);
}

/* ── Features ── */
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

/* ── Messages ── */
.message {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-muted);
}

.message.error {
  color: var(--color-danger);
}

/* ── Responsive ── */
@media (max-width: 1400px) {
  .pricing-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .pricing-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .pricing-hero {
    text-align: left;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
