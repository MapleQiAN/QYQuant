<script setup lang="ts">
import type { UserStrategyItem } from '../../types/User'

defineProps<{
  items: UserStrategyItem[]
  loading?: boolean
  hasMore?: boolean
}>()

defineEmits<{
  (event: 'load-more'): void
}>()

function formatPercent(value: number) {
  return `${value.toFixed(2)}%`
}
</script>

<template>
  <section class="list-shell">
    <p v-if="loading && !items.length" class="status">策略加载中...</p>
    <p v-else-if="!items.length" class="status">该用户暂未发布策略。</p>
    <div v-else class="grid">
      <article v-for="item in items" :key="item.id" class="strategy-card">
        <div class="card-top">
          <div>
            <h3 class="title">{{ item.name }}</h3>
            <p class="category">{{ item.category || '未分类' }}</p>
          </div>
        </div>

        <div class="metrics">
          <div class="metric">
            <span class="label">收益</span>
            <strong>{{ formatPercent(item.returns) }}</strong>
          </div>
          <div class="metric">
            <span class="label">回撤</span>
            <strong>{{ formatPercent(item.max_drawdown) }}</strong>
          </div>
          <div class="metric">
            <span class="label">胜率</span>
            <strong>{{ formatPercent(item.win_rate) }}</strong>
          </div>
        </div>

        <div v-if="item.tags.length" class="tags">
          <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </article>
    </div>

    <button v-if="hasMore" class="load-more" type="button" @click="$emit('load-more')">加载更多策略</button>
  </section>
</template>

<style scoped>
.list-shell {
  display: grid;
  gap: 16px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.strategy-card,
.status {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.title,
.category {
  margin: 0;
}

.title {
  color: var(--color-text-primary);
}

.category {
  margin-top: 6px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.metric {
  padding: 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.08), rgba(255, 255, 255, 0.96));
}

.label {
  display: block;
  color: var(--color-text-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.tag,
.load-more {
  border-radius: 999px;
}

.tag {
  padding: 6px 10px;
  background: rgba(15, 118, 110, 0.08);
  color: #0f766e;
  font-size: 12px;
}

.load-more {
  justify-self: center;
  border: 0;
  padding: 10px 18px;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font: inherit;
  cursor: pointer;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
