<template>
  <section class="admin-dashboard">
    <div class="container admin-dashboard__container">
      <header class="admin-dashboard__hero">
        <div>
          <p class="admin-dashboard__eyebrow">Admin Console</p>
          <h1>管理后台</h1>
          <p>系统概览、审核流程与任务监控都从这里进入，方便管理员集中处理平台运营事务。</p>
        </div>
        <div class="admin-dashboard__status">
          <span class="admin-dashboard__status-label">系统概览</span>
          <strong>{{ adminStore.overview?.scope || 'admin' }}</strong>
          <span>{{ adminStore.overview?.status || 'loading' }}</span>
        </div>
      </header>

      <div class="admin-dashboard__grid">
        <article class="admin-card">
          <h2>访问控制</h2>
          <p>后台路由和接口都启用了管理员校验，避免普通用户误入或越权操作。</p>
        </article>

        <article class="admin-card">
          <h2>审计留痕</h2>
          <p>关键管理动作会持续写入审计日志，方便排查争议、回溯处理过程。</p>
        </article>

        <article class="admin-card admin-card--accent">
          <h2>任务监控</h2>
          <p>查看回测队列、识别疑似卡死任务，并在必要时执行人工终止。</p>
          <RouterLink
            class="admin-card__link"
            data-test="admin-backtest-monitor-link"
            to="/admin/backtest-monitor"
          >
            进入任务监控
          </RouterLink>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()

onMounted(() => {
  void adminStore.loadOverview()
})
</script>

<style scoped>
.admin-dashboard {
  width: 100%;
}

.admin-dashboard__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.admin-dashboard__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(11, 107, 203, 0.18), transparent 45%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.92));
  color: #f8fafc;
  box-shadow: 0 24px 56px rgba(15, 23, 42, 0.18);
}

.admin-dashboard__hero h1,
.admin-dashboard__hero p {
  margin: 0;
}

.admin-dashboard__hero h1 {
  margin-bottom: var(--spacing-sm);
  font-size: clamp(2rem, 3vw, 2.8rem);
}

.admin-dashboard__eyebrow {
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-sm);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(191, 219, 254, 0.92);
}

.admin-dashboard__status {
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--spacing-md);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.24);
}

.admin-dashboard__status-label {
  color: rgba(191, 219, 254, 0.88);
  font-size: var(--font-size-sm);
}

.admin-dashboard__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.admin-card {
  padding: var(--spacing-lg);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.96));
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.admin-card--accent {
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.14), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(239, 246, 255, 0.96));
}

.admin-card h2,
.admin-card p {
  margin: 0;
}

.admin-card h2 {
  margin-bottom: var(--spacing-sm);
}

.admin-card__link {
  display: inline-flex;
  margin-top: var(--spacing-md);
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

@media (max-width: 960px) {
  .admin-dashboard__hero {
    flex-direction: column;
  }

  .admin-dashboard__grid {
    grid-template-columns: 1fr;
  }
}
</style>
