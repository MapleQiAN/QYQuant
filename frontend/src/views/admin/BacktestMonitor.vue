<template>
  <section class="backtest-monitor">
    <div class="container backtest-monitor__container">
      <header class="backtest-monitor__hero">
        <div>
          <p class="backtest-monitor__eyebrow">Admin Console</p>
          <h1>回测任务监控</h1>
          <p>聚合回测队列的关键指标，并为疑似卡死任务提供人工终止入口。</p>
        </div>
        <div class="backtest-monitor__actions">
          <RouterLink class="backtest-monitor__back" to="/admin">返回后台首页</RouterLink>
          <button
            type="button"
            class="backtest-monitor__refresh"
            data-test="monitor-refresh"
            :disabled="adminStore.queueStatsLoading"
            @click="refresh"
          >
            手动刷新
          </button>
        </div>
      </header>

      <section class="backtest-monitor__stats">
        <article class="metric-card" data-test="metric-pending">
          <span class="metric-card__label">排队中</span>
          <strong>{{ adminStore.queueStats.pending }}</strong>
        </article>
        <article class="metric-card" data-test="metric-running">
          <span class="metric-card__label">运行中</span>
          <strong>{{ adminStore.queueStats.running }}</strong>
        </article>
        <article class="metric-card" data-test="metric-avg-duration">
          <span class="metric-card__label">平均耗时</span>
          <strong>{{ formatDuration(adminStore.queueStats.avgDuration) }}</strong>
        </article>
        <article class="metric-card" data-test="metric-failure-rate">
          <span class="metric-card__label">1 小时失败率</span>
          <strong>{{ formatRate(adminStore.queueStats.failureRate1h) }}</strong>
        </article>
      </section>

      <section class="backtest-monitor__panel">
        <div class="backtest-monitor__panel-header">
          <div>
            <p class="backtest-monitor__panel-eyebrow">Suspected Stuck Jobs</p>
            <h2>疑似卡死任务</h2>
          </div>
        </div>

        <div v-if="adminStore.queueStatsLoading" class="backtest-monitor__empty">
          正在加载队列信息...
        </div>

        <div v-else-if="!adminStore.stuckJobs.length" class="backtest-monitor__empty">
          当前没有疑似卡死的回测任务。
        </div>

        <div v-else class="backtest-monitor__list">
          <article
            v-for="job in adminStore.stuckJobs"
            :key="job.jobId"
            class="job-card"
          >
            <div class="job-card__header">
              <div>
                <p class="job-card__meta">{{ job.jobId }}</p>
                <h3>{{ job.strategyName || '未命名策略' }}</h3>
              </div>
              <span class="job-card__badge">已运行 {{ formatDuration(job.runningDurationSeconds) }}</span>
            </div>

            <dl class="job-card__grid">
              <div>
                <dt>用户 ID</dt>
                <dd>{{ job.userId || '-' }}</dd>
              </div>
              <div>
                <dt>策略 ID</dt>
                <dd>{{ job.strategyId || '-' }}</dd>
              </div>
              <div>
                <dt>开始时间</dt>
                <dd>{{ formatDate(job.startedAt) }}</dd>
              </div>
            </dl>

            <div class="job-card__actions">
              <button
                type="button"
                class="job-card__button"
                :data-test="`terminate-job-${job.jobId}`"
                :disabled="isTerminating(job.jobId)"
                @click="openTerminateDialog(job.jobId)"
              >
                终止任务
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-if="dialog.open && activeJob" class="terminate-dialog__backdrop">
      <div class="terminate-dialog" role="dialog" aria-modal="true">
        <div class="terminate-dialog__header">
          <div>
            <p class="terminate-dialog__eyebrow">Manual Intervention</p>
            <h3>终止回测任务</h3>
          </div>
          <button type="button" class="terminate-dialog__close" @click="closeTerminateDialog">取消</button>
        </div>

        <p class="terminate-dialog__summary">
          将终止任务 <strong>{{ activeJob.jobId }}</strong>，策略为
          <strong>{{ activeJob.strategyName || '未命名策略' }}</strong>。
        </p>

        <textarea
          v-model="dialog.note"
          data-test="terminate-note"
          class="terminate-dialog__textarea"
          rows="4"
          maxlength="500"
          placeholder="可选：补充管理员备注，将展示在站内通知与审计日志中"
        />

        <div class="terminate-dialog__footer">
          <button type="button" class="terminate-dialog__ghost" @click="closeTerminateDialog">取消</button>
          <button
            type="button"
            class="terminate-dialog__danger"
            data-test="confirm-terminate"
            :disabled="isTerminating(activeJob.jobId)"
            @click="confirmTerminate"
          >
            确认终止
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { toast } from '../../lib/toast'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()
const dialog = reactive({
  open: false,
  jobId: '',
  note: ''
})

const activeJob = computed(() =>
  adminStore.stuckJobs.find((item) => item.jobId === dialog.jobId) ?? null
)

onMounted(() => {
  void adminStore.loadQueueStats()
})

function refresh() {
  void adminStore.loadQueueStats()
}

function openTerminateDialog(jobId: string) {
  dialog.open = true
  dialog.jobId = jobId
  dialog.note = ''
}

function closeTerminateDialog() {
  dialog.open = false
  dialog.jobId = ''
  dialog.note = ''
}

function isTerminating(jobId: string): boolean {
  return Boolean(adminStore.terminatingJobs?.[jobId])
}

async function confirmTerminate() {
  if (!activeJob.value) return

  try {
    await adminStore.terminateJob(activeJob.value.jobId, normalizedNote())
    toast.success('回测任务已终止')
    closeTerminateDialog()
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

function normalizedNote(): string | undefined {
  const note = dialog.note.trim()
  return note || undefined
}

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const value = new Date(iso)
  if (Number.isNaN(value.getTime())) return iso

  const pad = (input: number) => String(input).padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}`
}

function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '0s'
  }

  const totalSeconds = Math.floor(seconds)
  const minutes = Math.floor(totalSeconds / 60)
  const remainSeconds = totalSeconds % 60
  if (minutes <= 0) {
    return `${remainSeconds}s`
  }
  if (remainSeconds === 0) {
    return `${minutes}m`
  }
  return `${minutes}m ${remainSeconds}s`
}

function formatRate(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return '0%'
  }
  return `${(value * 100).toFixed(1).replace(/\\.0$/, '')}%`
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '操作失败，请稍后重试'
}
</script>

<style scoped>
.backtest-monitor {
  width: 100%;
}

.backtest-monitor__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.backtest-monitor__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.18), transparent 42%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 94, 89, 0.92));
  color: #f8fafc;
}

.backtest-monitor__hero h1,
.backtest-monitor__hero p,
.backtest-monitor__panel-header h2,
.backtest-monitor__panel-header p {
  margin: 0;
}

.backtest-monitor__eyebrow,
.backtest-monitor__panel-eyebrow,
.terminate-dialog__eyebrow {
  margin-bottom: var(--spacing-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: var(--font-size-sm);
}

.backtest-monitor__eyebrow {
  color: rgba(167, 243, 208, 0.92);
}

.backtest-monitor__panel-eyebrow,
.terminate-dialog__eyebrow {
  color: var(--color-text-secondary);
}

.backtest-monitor__actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.backtest-monitor__back,
.backtest-monitor__refresh,
.job-card__button,
.terminate-dialog__ghost,
.terminate-dialog__danger,
.terminate-dialog__close {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  border: none;
  font: inherit;
}

.backtest-monitor__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(248, 250, 252, 0.12);
  color: #f8fafc;
  text-decoration: none;
}

.backtest-monitor__refresh {
  background: #f8fafc;
  color: #0f172a;
  cursor: pointer;
}

.backtest-monitor__refresh:disabled,
.job-card__button:disabled,
.terminate-dialog__danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.backtest-monitor__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.metric-card,
.backtest-monitor__panel,
.job-card,
.terminate-dialog {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.metric-card {
  padding: var(--spacing-lg);
  border-radius: 22px;
}

.metric-card__label {
  display: block;
  margin-bottom: 10px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.metric-card strong {
  font-size: clamp(1.6rem, 2vw, 2.2rem);
  color: var(--color-text-primary);
}

.backtest-monitor__panel {
  padding: var(--spacing-lg);
  border-radius: 24px;
}

.backtest-monitor__list {
  display: grid;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.backtest-monitor__empty {
  margin-top: var(--spacing-md);
  padding: var(--spacing-xl);
  border-radius: 20px;
  background: rgba(241, 245, 249, 0.8);
  color: var(--color-text-secondary);
  text-align: center;
}

.job-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-radius: 24px;
}

.job-card__header,
.job-card__actions,
.terminate-dialog__header,
.terminate-dialog__footer {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: center;
}

.job-card__meta {
  margin: 0 0 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.job-card h3,
.job-card__grid dt,
.job-card__grid dd,
.terminate-dialog h3,
.terminate-dialog__summary {
  margin: 0;
}

.job-card__badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.job-card__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.job-card__grid div {
  padding: 14px;
  border-radius: 18px;
  background: rgba(241, 245, 249, 0.85);
}

.job-card__grid dt {
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.job-card__button,
.terminate-dialog__danger {
  background: #b91c1c;
  color: #f8fafc;
  cursor: pointer;
}

.terminate-dialog__ghost,
.terminate-dialog__close {
  background: rgba(148, 163, 184, 0.14);
  color: #334155;
  cursor: pointer;
}

.terminate-dialog__backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(6px);
}

.terminate-dialog {
  width: min(560px, 100%);
  padding: var(--spacing-lg);
  border-radius: 24px;
}

.terminate-dialog__summary {
  margin: var(--spacing-md) 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.terminate-dialog__textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 18px;
  resize: vertical;
  font: inherit;
}

@media (max-width: 960px) {
  .backtest-monitor__hero,
  .backtest-monitor__actions,
  .job-card__header,
  .job-card__actions,
  .terminate-dialog__header,
  .terminate-dialog__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .backtest-monitor__stats,
  .job-card__grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .backtest-monitor__stats,
  .job-card__grid {
    grid-template-columns: 1fr;
  }
}
</style>
