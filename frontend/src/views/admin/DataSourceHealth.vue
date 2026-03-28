<template>
  <section class="data-source-health">
    <div class="container data-source-health__container">
      <header class="data-source-health__hero">
        <div>
          <p class="data-source-health__eyebrow">Data Source</p>
          <h1>JQData 健康监控</h1>
          <p>展示最近一次持久化健康检查结果，不会在页面内直接触发真实探测。</p>
        </div>
        <button
          class="data-source-health__refresh"
          data-test="data-source-refresh"
          type="button"
          :disabled="adminStore.dataSourceHealthLoading"
          @click="refresh"
        >
          {{ adminStore.dataSourceHealthLoading ? '刷新中...' : '手动刷新' }}
        </button>
      </header>

      <article class="data-source-health__status-card">
        <div class="data-source-health__status-head">
          <div>
            <p class="data-source-health__source">JQData</p>
            <h2>当前健康状态</h2>
          </div>
          <span
            class="status-pill"
            :class="`status-pill--${adminStore.dataSourceHealth.statusColor}`"
            data-test="data-source-status"
          >
            {{ adminStore.dataSourceHealth.statusLabel }}
          </span>
        </div>

        <dl class="data-source-health__grid">
          <div class="metric-card">
            <dt>最近检查时间</dt>
            <dd>{{ adminStore.dataSourceHealth.lastCheckedAt || '暂无' }}</dd>
          </div>
          <div class="metric-card">
            <dt>最近成功时间</dt>
            <dd>{{ adminStore.dataSourceHealth.lastSuccessAt || '暂无' }}</dd>
          </div>
          <div class="metric-card">
            <dt>最近失败时间</dt>
            <dd>{{ adminStore.dataSourceHealth.lastFailureAt || '暂无' }}</dd>
          </div>
          <div class="metric-card">
            <dt>连续失败次数</dt>
            <dd>{{ adminStore.dataSourceHealth.consecutiveFailures }}</dd>
          </div>
        </dl>

        <section class="data-source-health__error-panel">
          <h3>最近错误</h3>
          <p>{{ adminStore.dataSourceHealth.lastErrorMessage || '当前没有错误信息。' }}</p>
        </section>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()

function refresh() {
  void adminStore.loadDataSourceHealth()
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.data-source-health {
  width: 100%;
}

.data-source-health__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.data-source-health__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(5, 150, 105, 0.16), transparent 42%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(31, 41, 55, 0.94));
  color: var(--color-text-inverse);
  box-shadow: var(--shadow-lg);
}

.data-source-health__hero h1,
.data-source-health__hero p {
  margin: 0;
}

.data-source-health__eyebrow {
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-sm);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(167, 243, 208, 0.92);
}

.data-source-health__refresh {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  background: rgba(255, 255, 255, 0.12);
  color: inherit;
  font-weight: 600;
  cursor: pointer;
}

.data-source-health__refresh:disabled {
  cursor: wait;
  opacity: 0.7;
}

.data-source-health__status-card {
  padding: var(--spacing-xl);
  border-radius: 28px;
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border-light);
}

.data-source-health__status-head {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.data-source-health__status-head h2,
.data-source-health__source,
.data-source-health__error-panel h3,
.data-source-health__error-panel p {
  margin: 0;
}

.data-source-health__source {
  margin-bottom: 6px;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 92px;
  padding: 10px 16px;
  border-radius: 999px;
  font-weight: 700;
}

.status-pill--green {
  background: rgba(16, 185, 129, 0.14);
  color: var(--color-success);
}

.status-pill--red {
  background: rgba(239, 68, 68, 0.14);
  color: var(--color-danger);
}

.status-pill--gray {
  background: rgba(148, 163, 184, 0.18);
  color: var(--color-text-secondary);
}

.data-source-health__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin: 0 0 var(--spacing-lg);
}

.metric-card {
  margin: 0;
  padding: var(--spacing-md);
  border-radius: 20px;
  background: var(--color-surface-hover);
}

.metric-card dt {
  margin-bottom: 6px;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.metric-card dd {
  margin: 0;
  font-weight: 600;
  word-break: break-word;
}

.data-source-health__error-panel {
  padding: var(--spacing-md);
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.04);
}

@media (max-width: 960px) {
  .data-source-health__hero,
  .data-source-health__status-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .data-source-health__grid {
    grid-template-columns: 1fr;
  }
}
</style>
