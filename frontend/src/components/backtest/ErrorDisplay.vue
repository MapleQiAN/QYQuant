<template>
  <section class="card error-card">
    <div class="error-header">
      <div>
        <p class="error-kicker">策略执行失败</p>
        <h2 class="error-title">{{ error.type }}</h2>
      </div>
      <span v-if="error.line" class="error-line">第 {{ error.line }} 行</span>
    </div>

    <p class="error-message">{{ error.message }}</p>
    <p v-if="error.suggestion" class="error-suggestion">{{ error.suggestion }}</p>

    <div v-if="error.example_code" class="code-block">
      <div class="code-header">
        <span>修复示例</span>
        <button type="button" class="copy-button" @click="copyExampleCode">复制</button>
      </div>
      <pre><code>{{ error.example_code }}</code></pre>
    </div>

    <details class="packages-panel">
      <summary>查看支持的依赖库</summary>
      <p v-if="loading" class="packages-loading">加载中...</p>
      <ul v-else class="packages-list">
        <li v-for="item in supportedPackages" :key="item.name" class="packages-item">
          <strong>{{ item.name }}</strong>
          <span>{{ item.version }}</span>
          <span>{{ item.description }}</span>
        </li>
      </ul>
    </details>
  </section>
</template>

<script setup lang="ts">
import type { StructuredBacktestError, SupportedPackage } from '../../types/Backtest'

const props = defineProps<{
  error: StructuredBacktestError
  supportedPackages: SupportedPackage[]
  loading?: boolean
}>()

async function copyExampleCode() {
  if (!props.error.example_code || !navigator?.clipboard?.writeText) {
    return
  }
  await navigator.clipboard.writeText(props.error.example_code)
}
</script>

<style scoped>
.error-card {
  padding: var(--spacing-lg);
  border: 1px solid rgba(185, 28, 28, 0.18);
  background:
    linear-gradient(145deg, rgba(255, 247, 237, 0.98), rgba(255, 255, 255, 0.94)),
    var(--color-surface);
}

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.error-kicker {
  margin: 0 0 6px;
  font-size: var(--font-size-sm);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #b45309;
}

.error-title {
  margin: 0;
  color: #991b1b;
}

.error-line {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(185, 28, 28, 0.08);
  color: #991b1b;
  font-weight: var(--font-weight-semibold);
}

.error-message,
.error-suggestion {
  margin: 0 0 var(--spacing-sm);
  line-height: 1.7;
  color: var(--color-text-primary);
}

.code-block {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: #111827;
  margin-top: var(--spacing-md);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  color: #e5e7eb;
  background: rgba(255, 255, 255, 0.06);
}

.copy-button {
  border: 0;
  border-radius: 999px;
  padding: 6px 12px;
  background: #f59e0b;
  color: #111827;
  cursor: pointer;
}

pre {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
  color: #f9fafb;
}

.packages-panel {
  margin-top: var(--spacing-md);
}

.packages-panel summary {
  cursor: pointer;
  color: #1d4ed8;
  font-weight: var(--font-weight-semibold);
}

.packages-list {
  list-style: none;
  margin: var(--spacing-sm) 0 0;
  padding: 0;
  display: grid;
  gap: var(--spacing-sm);
}

.packages-item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: rgba(29, 78, 216, 0.04);
}
</style>
