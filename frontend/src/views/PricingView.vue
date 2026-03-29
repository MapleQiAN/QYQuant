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
              <path d="M8 1.5A6.5 6.5 0 1 0 14.5 8 6.507 6.507 0 0 0 8 1.5zm.75 9.75h-1.5V7.25h1.5zm0-5h-1.5v-1.5h1.5z" fill="currentColor"/>
            </svg>
            <span class="pricing-card__quota">
              {{ plan.quota === null ? '无限回测次数' : `${plan.quota} 次 / 月` }}
            </span>
          </div>

          <p class="pricing-card__description">{{ plan.description }}</p>

          <!-- CTA -->
          <div class="pricing-card__actions">
            <template v-if="plan.level !== 'free' && currentPlanLevel !== plan.level">
              <button
                class="btn btn-cta btn-wechat"
                type="button"
                :disabled="submitting"
                @click="startCheckout(plan.level, 'wechat')"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" class="btn-icon" aria-hidden="true">
                  <path d="M8.5 13.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm5 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
                  <path fill-rule="evenodd" d="M3.5 9.25C3.5 5.798 7.358 3 12 3s8.5 2.798 8.5 6.25c0 3.453-3.858 6.25-8.5 6.25a10.3 10.3 0 0 1-2.125-.22l-2.262 1.508a.5.5 0 0 1-.769-.427l.12-2.143A6.27 6.27 0 0 1 3.5 9.25z" clip-rule="evenodd"/>
                </svg>
                微信支付
              </button>
              <button
                class="btn btn-cta btn-alipay"
                type="button"
                :disabled="submitting"
                @click="startCheckout(plan.level, 'alipay')"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" class="btn-icon" aria-hidden="true">
                  <path d="M3 4a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4zm2 1v14h14V5H5z"/>
                  <path d="M9 10h6m-3-3v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                支付宝
              </button>
            </template>
            <div v-else-if="plan.level === 'free'" class="btn btn-disabled" aria-disabled="true">
              免费体验套餐
            </div>
            <div v-else class="btn btn-disabled" aria-disabled="true">
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
              <!-- Check icon -->
              <span v-if="feature.included" class="feature-icon feature-icon--check" aria-hidden="true">
                <svg viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" fill="currentColor" opacity="0.15"/>
                  <path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
              <!-- X icon -->
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

      <p v-if="actionError" class="message error">{{ actionError }}</p>

      <!-- Confirm payment modal -->
      <div v-if="pendingOrder" class="modal-backdrop" @click.self="cancelConfirmation">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <h2 id="modal-title" class="modal__title">确认支付</h2>
          <p class="modal__text">套餐：{{ planLabel(pendingOrder.plan_level) }}</p>
          <p class="modal__text">金额：¥{{ pendingOrder.amount }}</p>
          <p class="modal__text">支付方式：{{ pendingOrder.provider === 'wechat' ? '微信支付' : '支付宝' }}</p>
          <p class="modal__terms">确认后即表示你同意《服务条款》并继续完成支付。</p>
          <div class="modal__actions">
            <button class="btn btn-secondary" type="button" @click="cancelConfirmation">取消</button>
            <button class="btn btn-primary" type="button" @click="confirmPayment">确认并前往支付</button>
          </div>
        </div>
      </div>

      <!-- WeChat pay QR modal -->
      <div v-if="wechatPayUrl" class="modal-backdrop" @click.self="wechatPayUrl = ''">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="wechat-modal-title">
          <h2 id="wechat-modal-title" class="modal__title">微信支付</h2>
          <p class="modal__text">请使用微信扫描下方二维码，或打开支付链接继续完成支付。</p>
          <img class="payment-qr" :src="wechatPayUrl" alt="微信支付二维码" />
          <a class="payment-link" :href="wechatPayUrl" target="_blank" rel="noopener">打开微信支付</a>
          <div class="modal__actions">
            <button class="btn btn-secondary" type="button" @click="wechatPayUrl = ''">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createPaymentOrder, type CreatePaymentOrderResponse, type PaymentProvider, type PlanLevel } from '../api/payments'
import { fetchMyQuota } from '../api/users'

interface PlanFeature {
  text: string
  included: boolean
}

const PLANS: {
  level: string
  name: string
  price: number
  quota: number | null
  description: string
  featured?: boolean
  features: PlanFeature[]
}[] = [
  {
    level: 'free',
    name: '免费',
    price: 0,
    quota: 10,
    description: '适合入门体验，熟悉平台功能。',
    features: [
      { text: '10 次回测 / 月', included: true },
      { text: '基础策略库访问', included: true },
      { text: '基础绩效指标', included: true },
      { text: '策略结果导出', included: false },
      { text: '高级回测参数配置', included: false },
      { text: '自定义数据源', included: false },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'lite',
    name: '轻量',
    price: 200,
    quota: 200,
    description: '适合个人量化爱好者，开展日常回测研究。',
    features: [
      { text: '200 次回测 / 月', included: true },
      { text: '基础策略库访问', included: true },
      { text: '基础绩效指标', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: false },
      { text: '自定义数据源', included: false },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'pro',
    name: '进阶',
    price: 500,
    quota: 500,
    description: '适合中频研究和更稳定的策略迭代工作。',
    featured: true,
    features: [
      { text: '500 次回测 / 月', included: true },
      { text: '完整策略库访问', included: true },
      { text: '高级绩效指标分析', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: true },
      { text: '自定义数据源', included: true },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'expert',
    name: '专业',
    price: 1000,
    quota: null,
    description: '不限回测次数，适合高频研究与团队协作。',
    features: [
      { text: '无限回测次数', included: true },
      { text: '完整策略库访问', included: true },
      { text: '高级绩效指标分析', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: true },
      { text: '自定义数据源', included: true },
      { text: '优先技术支持', included: true },
      { text: '高级 API 访问权限', included: true },
    ],
  },
]

const loading = ref(true)
const loadError = ref('')
const actionError = ref('')
const submitting = ref(false)
const isLoggedIn = ref(false)
const currentPlanLevel = ref<PlanLevel>('free')
const pendingOrder = ref<CreatePaymentOrderResponse | null>(null)
const wechatPayUrl = ref('')

const planMap = computed(() => Object.fromEntries(PLANS.map((plan) => [plan.level, plan])))

function planLabel(level: PlanLevel) {
  return planMap.value[level]?.name ?? level
}

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

async function startCheckout(planLevel: PlanLevel, provider: PaymentProvider) {
  if (!isLoggedIn.value) {
    actionError.value = '请先登录后再进行支付'
    return
  }
  actionError.value = ''
  submitting.value = true
  wechatPayUrl.value = ''

  try {
    pendingOrder.value = await createPaymentOrder({
      plan_level: planLevel,
      provider,
    })
  } catch (error: any) {
    actionError.value = error?.message || '支付订单创建失败'
  } finally {
    submitting.value = false
  }
}

function cancelConfirmation() {
  pendingOrder.value = null
}

function confirmPayment() {
  if (!pendingOrder.value) return

  if (pendingOrder.value.provider === 'alipay') {
    window.open(pendingOrder.value.pay_url, '_blank', 'noopener')
    pendingOrder.value = null
    return
  }

  wechatPayUrl.value = pendingOrder.value.pay_url
  pendingOrder.value = null
}

onMounted(() => {
  void loadQuota()
})
</script>

<style scoped>
/* ── Page Layout ── */
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
  background: linear-gradient(
    160deg,
    var(--color-primary-bg) 0%,
    var(--color-surface) 60%
  );
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
  min-height: 24px;
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
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.pricing-card__price-row {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.pricing-card__currency {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  align-self: flex-start;
  margin-top: 6px;
}

.pricing-card__price {
  color: var(--color-text-primary);
  font-size: 2.4rem;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.pricing-card__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin-left: 2px;
}

/* ── Quota ── */
.pricing-card__quota-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.quota-icon {
  width: 14px;
  height: 14px;
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
  line-height: 1.6;
  min-height: 40px;
}

/* ── CTA Buttons ── */
.pricing-card__actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.btn-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: opacity 150ms ease, transform 150ms ease;
}

.btn-cta:hover:not(:disabled) {
  opacity: 0.88;
  transform: translateY(-1px);
}

.btn-cta:active:not(:disabled) {
  transform: translateY(0);
}

.btn-cta:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-wechat {
  background: #07C160;
  color: #fff;
}

.btn-alipay {
  background: #1677FF;
  color: #fff;
}

.btn-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.btn-disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-hover);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border: 1px solid var(--color-border);
  cursor: default;
  user-select: none;
}

/* ── Divider ── */
.pricing-card__divider {
  height: 1px;
  background: var(--color-border);
  margin: 0 calc(-1 * var(--spacing-sm));
}

/* ── Feature List ── */
.feature-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.feature-icon--check {
  color: var(--color-success);
}

.feature-icon--cross {
  color: var(--color-text-muted);
}

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

/* ── Modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-overlay);
  z-index: 100;
}

.modal {
  width: min(480px, 100%);
  padding: var(--spacing-lg);
  border-radius: var(--radius-xl);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
}

.modal__title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
}

.modal__text,
.modal__terms {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.payment-qr {
  display: block;
  width: min(240px, 100%);
  margin: var(--spacing-md) auto;
  border-radius: var(--radius-md);
  background: var(--color-surface-hover);
}

.payment-link {
  display: inline-flex;
  color: var(--color-primary);
  text-decoration: none;
  font-size: var(--font-size-sm);
}

.payment-link:hover {
  text-decoration: underline;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .pricing-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .pricing-hero {
    text-align: left;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .modal__actions {
    flex-direction: column;
  }
}
</style>
