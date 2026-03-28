<template>
  <section class="strategy-review">
    <div class="container strategy-review__container">
      <header class="strategy-review__hero">
        <div>
          <p class="strategy-review__eyebrow">Admin Console</p>
          <h1>策略审核队列</h1>
          <p>处理待上架策略，保持 marketplace 可见内容与审核结果一致。</p>
        </div>
        <RouterLink class="strategy-review__back" to="/admin">返回后台首页</RouterLink>
      </header>

      <div v-if="adminStore.reviewQueueLoading" class="strategy-review__empty">
        正在加载待审核策略...
      </div>

      <div v-else-if="!adminStore.reviewQueue.length" class="strategy-review__empty" data-test="review-empty">
        当前没有待审核策略。
      </div>

      <div v-else class="strategy-review__list">
        <article
          v-for="item in adminStore.reviewQueue"
          :key="item.id"
          class="review-card"
          :data-test="`review-card-${item.id}`"
        >
          <div class="review-card__header">
            <div>
              <p class="review-card__meta">{{ item.authorNickname || '匿名作者' }} · {{ formatDate(item.createdAt) }}</p>
              <h2>{{ item.title }}</h2>
            </div>
            <span class="review-card__status">待审核</span>
          </div>

          <p class="review-card__description">{{ item.description || '暂无策略描述。' }}</p>

          <dl class="review-card__grid">
            <div>
              <dt>分类</dt>
              <dd>{{ item.category || '-' }}</dd>
            </div>
            <div>
              <dt>标签</dt>
              <dd>{{ item.tags.join('、') || '-' }}</dd>
            </div>
            <div>
              <dt>Sharpe</dt>
              <dd>{{ metricValue(item.displayMetrics, 'sharpe_ratio') }}</dd>
            </div>
            <div>
              <dt>最大回撤</dt>
              <dd>{{ metricValue(item.displayMetrics, 'max_drawdown') }}</dd>
            </div>
            <div>
              <dt>总收益</dt>
              <dd>{{ metricValue(item.displayMetrics, 'total_return') }}</dd>
            </div>
          </dl>

          <textarea
            :data-test="`reject-reason-${item.id}`"
            v-model="rejectReasons[item.id]"
            class="review-card__reason"
            placeholder="拒绝时填写原因"
            rows="3"
          />

          <div class="review-card__actions">
            <button
              class="review-card__button review-card__button--approve"
              type="button"
              :data-test="`approve-${item.id}`"
              :disabled="isSubmitting(item.id)"
              @click="approve(item.id)"
            >
              通过
            </button>
            <button
              class="review-card__button review-card__button--reject"
              type="button"
              :data-test="`reject-${item.id}`"
              :disabled="isSubmitting(item.id)"
              @click="reject(item.id)"
            >
              拒绝
            </button>
          </div>
        </article>
      </div>

      <nav
        v-if="!adminStore.reviewQueueLoading && adminStore.reviewQueueMeta.total > adminStore.reviewQueueMeta.perPage"
        class="strategy-review__pagination"
      >
        <button
          :disabled="adminStore.reviewQueueMeta.page <= 1"
          @click="goToPage(adminStore.reviewQueueMeta.page - 1)"
        >
          上一页
        </button>
        <span>
          第 {{ adminStore.reviewQueueMeta.page }} / {{ totalPages }} 页
          （共 {{ adminStore.reviewQueueMeta.total }} 条）
        </span>
        <button
          :disabled="adminStore.reviewQueueMeta.page >= totalPages"
          @click="goToPage(adminStore.reviewQueueMeta.page + 1)"
        >
          下一页
        </button>
      </nav>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { toast } from '../../lib/toast'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()
const rejectReasons = reactive<Record<string, string>>({})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(adminStore.reviewQueueMeta.total / adminStore.reviewQueueMeta.perPage))
)

onMounted(() => {
  void adminStore.loadPendingReviews()
})

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return iso
  }
}

function goToPage(page: number) {
  void adminStore.loadPendingReviews(page)
}

function metricValue(metrics: Record<string, unknown>, key: string): string {
  const value = metrics?.[key]
  return value == null || value === '' ? '-' : String(value)
}

function isSubmitting(strategyId: string): boolean {
  return Boolean(adminStore.reviewSubmitting?.[strategyId])
}

async function approve(strategyId: string) {
  try {
    await adminStore.reviewStrategy(strategyId, { status: 'approved' })
    toast.success('审核已通过')
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

async function reject(strategyId: string) {
  const reason = (rejectReasons[strategyId] || '').trim()
  if (!reason) {
    toast.error('请填写拒绝原因')
    return
  }

  try {
    await adminStore.reviewStrategy(strategyId, { status: 'rejected', reason })
    toast.success('审核已拒绝')
    rejectReasons[strategyId] = ''
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '操作失败，请稍后重试'
}
</script>

<style scoped>
.strategy-review {
  width: 100%;
}

.strategy-review__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.strategy-review__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.2), transparent 40%),
    linear-gradient(140deg, rgba(15, 23, 42, 0.96), rgba(17, 94, 89, 0.92));
  color: var(--color-text-inverse);
}

.strategy-review__hero h1,
.strategy-review__hero p {
  margin: 0;
}

.strategy-review__hero h1 {
  margin-bottom: var(--spacing-sm);
  font-size: clamp(2rem, 3vw, 2.6rem);
}

.strategy-review__eyebrow {
  margin-bottom: var(--spacing-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: var(--font-size-sm);
  color: rgba(167, 243, 208, 0.92);
}

.strategy-review__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-text-inverse);
  text-decoration: none;
}

.strategy-review__list {
  display: grid;
  gap: var(--spacing-md);
}

.strategy-review__empty {
  padding: var(--spacing-xl);
  border-radius: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-secondary);
  text-align: center;
}

.review-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-radius: 24px;
  border: 1px solid var(--color-border-light);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.review-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.review-card__header h2,
.review-card__description,
.review-card__meta,
.review-card__grid dd,
.review-card__grid dt {
  margin: 0;
}

.review-card__meta {
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.review-card__status {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  color: var(--color-warning);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.review-card__description {
  color: var(--color-text-secondary);
}

.review-card__grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.review-card__grid div {
  padding: 14px;
  border-radius: 18px;
  background: var(--color-surface-hover);
}

.review-card__grid dt {
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.review-card__grid dd {
  font-weight: 600;
}

.review-card__reason {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  resize: vertical;
  font: inherit;
}

.review-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.review-card__button {
  min-width: 112px;
  min-height: 42px;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.review-card__button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.review-card__button--approve {
  background: var(--color-success);
  color: var(--color-text-inverse);
}

.review-card__button--reject {
  background: rgba(239, 68, 68, 0.12);
  color: var(--color-danger);
}

.strategy-review__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
}

.strategy-review__pagination button {
  min-width: 80px;
  min-height: 38px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font: inherit;
  cursor: pointer;
}

.strategy-review__pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.strategy-review__pagination span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

@media (max-width: 960px) {
  .strategy-review__hero,
  .review-card__header,
  .review-card__actions {
    flex-direction: column;
  }

  .review-card__grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .review-card__grid {
    grid-template-columns: 1fr;
  }
}
</style>
