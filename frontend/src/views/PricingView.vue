<template>
  <section class="view pricing-view">
    <!-- Background financial atmosphere -->
    <div class="pricing-bg" aria-hidden="true">
      <div class="pricing-bg__grid"></div>
      <div class="pricing-bg__glow pricing-bg__glow--1"></div>
      <div class="pricing-bg__glow pricing-bg__glow--2"></div>
      <svg class="pricing-bg__chart" viewBox="0 0 1200 200" preserveAspectRatio="none">
        <polyline points="0,160 80,140 160,150 240,110 320,130 400,90 480,100 560,60 640,80 720,40 800,65 880,30 960,50 1040,20 1120,35 1200,10" />
        <polyline class="pricing-bg__chart--secondary" points="0,180 80,170 160,175 240,155 320,165 400,140 480,150 560,125 640,135 720,110 800,120 880,100 960,115 1040,95 1120,105 1200,85" />
      </svg>
    </div>

    <div class="container pricing-page">
      <header class="pricing-hero">
        <div class="pricing-hero__badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/>
          </svg>
          <span>套餐升级</span>
        </div>
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
          v-for="(plan, index) in PLANS"
          :key="plan.level"
          class="pricing-card"
          :class="{
            'pricing-card--current': currentPlanLevel === plan.level,
            'pricing-card--lower-tier': isLoggedIn && isPlanTierLowerThanCurrent(plan.level) && currentPlanLevel !== plan.level,
            'pricing-card--featured': plan.featured && shouldShowFeatured,
            'pricing-card--ultra': plan.level === 'ultra',
          }"
          :style="{ '--card-delay': index * 80 + 'ms' }"
        >
          <!-- Decorative top accent -->
          <div class="pricing-card__accent" aria-hidden="true"></div>

          <!-- Badge row -->
          <div class="pricing-card__badges">
            <span v-if="plan.featured && shouldShowFeatured" class="badge badge--featured">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
              </svg>
              推荐
            </span>
            <span v-if="plan.level === 'ultra'" class="badge badge--ultra">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/>
              </svg>
              旗舰
            </span>
            <span v-if="currentPlanLevel === plan.level" class="badge badge--current">当前套餐</span>
          </div>

          <!-- Plan name & price -->
          <div class="pricing-card__header">
            <p class="pricing-card__name">{{ plan.name }}</p>
            <div v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__promo-tag">新用户首充</div>
            <div class="pricing-card__price-row">
              <span class="pricing-card__currency">¥</span>
              <span class="pricing-card__price">{{ firstPurchaseEligible && plan.promoPrice != null ? plan.promoPrice : plan.price }}</span>
              <span class="pricing-card__unit">/ 月</span>
              <span v-if="firstPurchaseEligible && plan.promoPrice != null" class="pricing-card__original-price">¥{{ plan.price }}</span>
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
              v-if="plan.level !== 'free' && currentPlanLevel !== plan.level && !isPlanTierLowerThanCurrent(plan.level)"
              class="btn btn-upgrade"
              :class="{
                'btn-upgrade--featured': plan.featured && shouldShowFeatured,
                'btn-upgrade--ultra': plan.level === 'ultra',
              }"
              type="button"
              @click="goToCheckout(plan.level)"
            >
              升级到 {{ plan.name }}
              <svg viewBox="0 0 16 16" fill="none" class="btn-arrow" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
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

/** True when the user does NOT already own Plus or a higher tier. */
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
/* ── Premium Color Tokens (theme-adaptive) ── */
.pricing-view {
  --gold: #9A7B3A;
  --gold-light: #B8944F;
  --gold-dim: rgba(154, 123, 58, 0.1);
  --gold-glow: rgba(154, 123, 58, 0.18);
  --gold-text: #7A6230;
  --card-bg: var(--color-surface);
  --card-bg-glass: rgba(255, 255, 255, 0.85);
  --card-featured-bg: linear-gradient(168deg, rgba(30, 90, 168, 0.06) 0%, var(--color-surface) 40%);
  --card-ultra-bg: linear-gradient(168deg, rgba(154, 123, 58, 0.06) 0%, var(--color-surface) 35%);
  --grid-line-color: rgba(154, 123, 58, 0.06);
  --glow-primary: rgba(30, 90, 168, 0.08);
  --glow-gold: rgba(154, 123, 58, 0.05);
  --chart-opacity: 0.08;
  --accent-ring-featured: rgba(30, 90, 168, 0.12);
  --accent-ring-ultra: rgba(154, 123, 58, 0.12);
  position: relative;
  width: 100%;
  overflow: hidden;
}

/* Dark theme overrides */
:root[data-theme="dark"] .pricing-view {
  --gold: #C9A962;
  --gold-light: #E2CA8A;
  --gold-dim: rgba(201, 169, 98, 0.15);
  --gold-glow: rgba(201, 169, 98, 0.25);
  --gold-text: #C9A962;
  --card-bg: var(--color-surface);
  --card-bg-glass: rgba(10, 15, 29, 0.7);
  --card-featured-bg: linear-gradient(168deg, rgba(30, 90, 168, 0.12) 0%, rgba(10, 15, 29, 0.8) 40%, rgba(10, 15, 29, 0.7) 100%);
  --card-ultra-bg: linear-gradient(168deg, rgba(201, 169, 98, 0.08) 0%, rgba(10, 15, 29, 0.85) 35%, rgba(10, 15, 29, 0.7) 100%);
  --grid-line-color: rgba(201, 169, 98, 0.03);
  --glow-primary: rgba(30, 90, 168, 0.2);
  --glow-gold: rgba(201, 169, 98, 0.1);
  --chart-opacity: 0.06;
  --accent-ring-featured: rgba(30, 90, 168, 0.1);
  --accent-ring-ultra: rgba(201, 169, 98, 0.08);
}

/* ── Atmospheric Background ── */
.pricing-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.pricing-bg__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--grid-line-color) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line-color) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 0%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 0%, transparent 70%);
}

.pricing-bg__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
}

.pricing-bg__glow--1 {
  width: 600px;
  height: 400px;
  top: -120px;
  left: 50%;
  transform: translateX(-50%);
  background: radial-gradient(circle, var(--glow-primary) 0%, transparent 70%);
}

.pricing-bg__glow--2 {
  width: 400px;
  height: 300px;
  top: 40px;
  right: 10%;
  background: radial-gradient(circle, var(--glow-gold) 0%, transparent 70%);
}

.pricing-bg__chart {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 200px;
  opacity: var(--chart-opacity);
}

.pricing-bg__chart polyline {
  fill: none;
  stroke: var(--gold);
  stroke-width: 2;
}

.pricing-bg__chart--secondary {
  stroke: var(--color-primary) !important;
  stroke-dasharray: 4 4;
}

/* ── Page Layout ── */
.pricing-page {
  position: relative;
  z-index: 1;
  padding-bottom: var(--spacing-xl);
}

/* ── Hero Section ── */
.pricing-hero {
  margin-bottom: var(--spacing-xl);
  text-align: center;
  padding-top: var(--spacing-md);
}

.pricing-hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  margin-bottom: var(--spacing-md);
  border-radius: var(--radius-full);
  background: var(--gold-dim);
  border: 1px solid var(--gold-glow);
  color: var(--gold-text);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.pricing-hero__title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
  font-size: clamp(1.6rem, 3vw, 2.2rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.pricing-hero__subtitle {
  margin: 0 auto;
  max-width: 480px;
  color: var(--color-text-muted);
  font-size: var(--font-size-md);
  line-height: 1.6;
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
  background: var(--card-bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 280ms ease, border-color 280ms ease, transform 280ms ease;
  position: relative;
  overflow: hidden;
  animation: cardReveal 500ms ease both;
  animation-delay: var(--card-delay, 0ms);
}

@keyframes cardReveal {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.pricing-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-hover);
  transform: translateY(-3px);
}

.pricing-card__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, var(--color-primary) 50%, transparent 100%);
  opacity: 0.4;
  transition: opacity 280ms ease;
}

.pricing-card:hover .pricing-card__accent {
  opacity: 0.8;
}

/* ── Current Plan ── */
.pricing-card--current {
  border-color: var(--color-primary-border);
}

/* ── Lower Tier Plan (user has a higher plan) ── */
.pricing-card--lower-tier {
  opacity: 0.65;
}

.pricing-card--lower-tier:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
  border-color: var(--color-border);
}

/* ── Featured Card (Plus) ── */
.pricing-card--featured {
  border-color: var(--color-primary);
  background: var(--card-featured-bg);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--color-primary-border), 0 0 30px var(--accent-ring-featured);
}

.pricing-card--featured .pricing-card__accent {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-primary), var(--color-accent), var(--color-primary), transparent);
  opacity: 0.8;
}

.pricing-card--featured:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg), 0 0 0 1px var(--color-primary-border), 0 0 40px var(--accent-ring-featured);
}

/* ── Ultra Card (Gold Premium) ── */
.pricing-card--ultra {
  border-color: var(--gold-glow);
  background: var(--card-ultra-bg);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--gold-dim), 0 0 30px var(--accent-ring-ultra);
}

.pricing-card--ultra .pricing-card__accent {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), var(--gold-light), var(--gold), transparent);
  opacity: 0.7;
}

.pricing-card--ultra:hover {
  border-color: var(--gold);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg), 0 0 0 1px var(--gold-glow), 0 0 30px var(--accent-ring-ultra);
}

.pricing-card--ultra .pricing-card__name {
  color: var(--gold-text);
}

.pricing-card--ultra .pricing-card__quota {
  color: var(--gold-text);
}

.pricing-card--ultra .quota-icon {
  color: var(--gold-text);
}

.pricing-card--ultra .pricing-card__divider {
  background: linear-gradient(90deg, transparent, var(--gold-dim), transparent);
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
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
  line-height: 1.6;
}

.badge--featured {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: #fff;
  box-shadow: 0 2px 8px var(--accent-ring-featured);
}

.badge--ultra {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  color: #fff;
  box-shadow: 0 2px 8px var(--gold-dim);
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
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
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
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.pricing-card--ultra .pricing-card__currency,
.pricing-card--ultra .pricing-card__price {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7a45 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  width: fit-content;
}

.pricing-card__original-price {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-decoration: line-through;
  margin-left: 6px;
  opacity: 0.7;
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
  font-weight: 600;
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
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.btn-upgrade::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 200ms ease;
}

.btn-upgrade:hover {
  background: var(--color-surface-active);
  border-color: var(--color-border-hover);
  transform: translateY(-1px);
}

.btn-upgrade:hover::before {
  opacity: 1;
}

.btn-upgrade:active {
  transform: translateY(0);
}

.btn-upgrade--featured {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-color: var(--color-primary);
  color: #fff;
  box-shadow: 0 2px 16px var(--accent-ring-featured);
}

.btn-upgrade--featured:hover {
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary) 100%);
  border-color: var(--color-primary-light);
  box-shadow: 0 4px 20px var(--accent-ring-featured);
}

.btn-upgrade--ultra {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  border-color: var(--gold);
  color: #fff;
  box-shadow: 0 2px 16px var(--gold-dim);
}

.btn-upgrade--ultra:hover {
  background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 100%);
  border-color: var(--gold-light);
  box-shadow: 0 4px 20px var(--gold-glow);
}

.btn-arrow {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  transition: transform 200ms ease;
}

.btn-upgrade:hover .btn-arrow {
  transform: translateX(2px);
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
  font-weight: 500;
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
  background: linear-gradient(90deg, transparent, var(--color-border), transparent);
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

.pricing-card--ultra .feature-icon--check { color: var(--gold-text); }

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
  gap: var(--spacing-lg);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--gold-dim);
}

.pricing-trust__item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.pricing-trust__item svg {
  color: var(--gold);
  opacity: 0.6;
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
  .pricing-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .pricing-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pricing-trust {
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }
}

@media (max-width: 560px) {
  .pricing-hero {
    text-align: left;
  }

  .pricing-hero__badge {
    margin-left: 0;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .pricing-trust {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
