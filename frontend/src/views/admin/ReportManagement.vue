<template>
  <section class="report-management">
    <div class="container report-management__container">
      <header class="report-management__hero">
        <div>
          <p class="report-management__eyebrow">Admin Console</p>
          <h1>举报管理</h1>
          <p>集中处理策略举报，对违规内容执行下架或驳回操作。</p>
        </div>
        <RouterLink class="report-management__back" to="/admin">返回后台首页</RouterLink>
      </header>

      <div v-if="adminStore.reportQueueLoading" class="report-management__empty">
        正在加载举报队列...
      </div>

      <div v-else-if="!adminStore.reportQueue.length" class="report-management__empty">
        当前没有待处理举报。
      </div>

      <div v-else class="report-management__list">
        <article
          v-for="item in adminStore.reportQueue"
          :key="item.id"
          class="report-card"
        >
          <div class="report-card__header">
            <div>
              <p class="report-card__meta">
                {{ item.reporterNickname || '匿名用户' }} 举报 · {{ formatDate(item.createdAt) }}
              </p>
              <h2>{{ item.strategyTitle }}</h2>
              <p class="report-card__author">作者：{{ item.strategyAuthorNickname || '未知作者' }}</p>
            </div>
            <span class="report-card__status">待处理</span>
          </div>

          <div class="report-card__reason">
            {{ item.reason }}
          </div>

          <textarea
            v-model="adminNotes[item.id]"
            :data-test="`admin-note-${item.id}`"
            class="report-card__note"
            rows="3"
            maxlength="500"
            placeholder="可选：补充管理员备注（最多 500 字）"
          />

          <div class="report-card__actions">
            <button
              type="button"
              class="report-card__button report-card__button--dismiss"
              :data-test="`dismiss-${item.id}`"
              :disabled="isResolving(item.id)"
              @click="dismiss(item.id)"
            >
              驳回举报
            </button>
            <button
              type="button"
              class="report-card__button report-card__button--takedown"
              :data-test="`takedown-${item.id}`"
              :disabled="isResolving(item.id)"
              @click="takedown(item.id)"
            >
              下架策略
            </button>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { toast } from '../../lib/toast'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()
const adminNotes = reactive<Record<string, string>>({})

onMounted(() => {
  void adminStore.loadPendingReports()
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

function isResolving(reportId: string): boolean {
  return Boolean(adminStore.reportResolving?.[reportId])
}

async function takedown(reportId: string) {
  const item = adminStore.reportQueue.find(r => r.id === reportId)
  const title = item?.strategyTitle || '该策略'
  if (!window.confirm(`确认下架策略「${title}」？此操作不可撤销。`)) return

  try {
    await adminStore.resolveReport(reportId, {
      action: 'takedown',
      adminNote: normalizedNote(reportId)
    })
    toast.success('已下架相关策略')
    adminNotes[reportId] = ''
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

async function dismiss(reportId: string) {
  try {
    await adminStore.resolveReport(reportId, {
      action: 'dismiss',
      adminNote: normalizedNote(reportId)
    })
    toast.success('已驳回举报')
    adminNotes[reportId] = ''
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

function normalizedNote(reportId: string): string | undefined {
  const note = (adminNotes[reportId] || '').trim()
  return note || undefined
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '操作失败，请稍后重试'
}
</script>

<style scoped>
.report-management__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.report-management__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(248, 113, 113, 0.18), transparent 40%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(127, 29, 29, 0.9));
  color: var(--color-text-inverse);
}

.report-management__hero h1,
.report-management__hero p {
  margin: 0;
}

.report-management__eyebrow {
  margin-bottom: var(--spacing-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: var(--font-size-sm);
  color: rgba(254, 202, 202, 0.92);
}

.report-management__back {
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

.report-management__empty {
  padding: var(--spacing-xl);
  border-radius: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-secondary);
  text-align: center;
}

.report-management__list {
  display: grid;
  gap: var(--spacing-md);
}

.report-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-radius: 24px;
  border: 1px solid var(--color-border-light);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.report-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.report-card__header h2,
.report-card__meta,
.report-card__author {
  margin: 0;
}

.report-card__meta,
.report-card__author {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.report-card__author {
  margin-top: 4px;
}

.report-card__status {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  color: var(--color-warning);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.report-card__reason {
  padding: 16px;
  border-radius: 18px;
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  line-height: 1.7;
}

.report-card__note {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  resize: vertical;
  font: inherit;
}

.report-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.report-card__button {
  min-width: 112px;
  min-height: 42px;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.report-card__button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.report-card__button--dismiss {
  background: rgba(148, 163, 184, 0.18);
  color: var(--color-text-secondary);
}

.report-card__button--takedown {
  background: var(--color-danger);
  color: var(--color-text-inverse);
}

@media (max-width: 960px) {
  .report-management__hero,
  .report-card__header,
  .report-card__actions {
    flex-direction: column;
  }
}
</style>
