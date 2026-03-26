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
          :class="{ 'pricing-card--current': currentPlanLevel === plan.level }"
        >
          <div class="pricing-card__header">
            <div>
              <p class="pricing-card__name">{{ plan.name }}</p>
              <h2 class="pricing-card__price">
                <span class="pricing-card__currency">¥</span>{{ plan.price }}
                <span class="pricing-card__unit">/ 月</span>
              </h2>
            </div>
            <span v-if="currentPlanLevel === plan.level" class="pricing-badge">当前套餐</span>
          </div>

          <p class="pricing-card__quota">
            {{ plan.quota === null ? '无限回测' : `${plan.quota} 次 / 月` }}
          </p>
          <p class="pricing-card__description">{{ plan.description }}</p>

          <div class="pricing-card__actions">
            <template v-if="plan.level !== 'free' && currentPlanLevel !== plan.level">
              <button
                class="btn btn-secondary"
                type="button"
                :disabled="submitting"
                @click="startCheckout(plan.level, 'wechat')"
              >
                微信支付
              </button>
              <button
                class="btn btn-primary"
                type="button"
                :disabled="submitting"
                @click="startCheckout(plan.level, 'alipay')"
              >
                支付宝
              </button>
            </template>
            <p v-else-if="plan.level === 'free'" class="pricing-card__hint">免费体验套餐</p>
            <p v-else class="pricing-card__hint">你当前正在使用此套餐</p>
          </div>
        </article>
      </div>

      <p v-if="actionError" class="message error">{{ actionError }}</p>

      <div v-if="pendingOrder" class="modal-backdrop">
        <div class="modal">
          <h2 class="modal__title">确认支付</h2>
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

      <div v-if="wechatPayUrl" class="modal-backdrop">
        <div class="modal">
          <h2 class="modal__title">微信支付</h2>
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
import { useRouter } from 'vue-router'
import { createPaymentOrder, type CreatePaymentOrderResponse, type PaymentProvider, type PlanLevel } from '../api/payments'
import { fetchMyQuota } from '../api/users'

const router = useRouter()

const PLANS = [
  { level: 'free', name: '免费', price: 0, quota: 10, description: '适合入门体验和熟悉平台。' },
  { level: 'lite', name: '轻量', price: 200, quota: 200, description: '适合个人量化爱好者开展日常回测。' },
  { level: 'pro', name: '进阶', price: 500, quota: 500, description: '适合中频研究和更稳定的策略迭代。' },
  { level: 'expert', name: '专业', price: 1000, quota: null, description: '不限回测次数，适合高频研究与团队协作。' },
] as const

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
  if (!pendingOrder.value) {
    return
  }

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
.view {
  width: 100%;
}

.pricing-page {
  padding-bottom: var(--spacing-xl);
}

.pricing-hero {
  margin-bottom: var(--spacing-lg);
}

.pricing-eyebrow {
  margin: 0 0 var(--spacing-xs);
  color: #0b6bcb;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.pricing-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.94)),
    linear-gradient(135deg, rgba(11, 107, 203, 0.08), rgba(255, 255, 255, 0));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.pricing-card--current {
  border-color: #0b6bcb;
  box-shadow: 0 18px 44px rgba(11, 107, 203, 0.18);
}

.pricing-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.pricing-card__name {
  margin: 0 0 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.pricing-card__price {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 2rem;
}

.pricing-card__currency,
.pricing-card__unit {
  font-size: var(--font-size-sm);
}

.pricing-badge {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(11, 107, 203, 0.12);
  color: #0b6bcb;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.pricing-card__quota {
  margin: 0;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.pricing-card__description {
  margin: 0;
  color: var(--color-text-muted);
  min-height: 48px;
}

.pricing-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: auto;
}

.pricing-card__hint {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.message {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-muted);
}

.message.error {
  color: var(--color-danger);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.48);
}

.modal {
  width: min(480px, 100%);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.2);
}

.modal__title {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
}

.modal__text,
.modal__terms {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text-secondary);
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
  background: var(--color-surface-alt);
}

.payment-link {
  display: inline-flex;
  color: #0b6bcb;
  text-decoration: none;
}

@media (max-width: 1100px) {
  .pricing-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .pricing-card__actions,
  .modal__actions {
    flex-direction: column;
  }
}
</style>
