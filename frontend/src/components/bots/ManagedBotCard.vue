<template>
  <article class="bot-card" :class="`bot-card--${bot.status}`">
    <div class="bot-card__header">
      <div>
        <span class="bot-card__name">{{ bot.name }}</span>
        <p class="bot-card__sub">{{ bot.strategyName }} · {{ bot.integrationDisplayName }}</p>
      </div>
      <span class="bot-card__badge">{{ statusLabel }}</span>
    </div>

    <div class="bot-card__metrics">
      <div class="metric">
        <span>托管金额</span>
        <strong>{{ formatMoney(bot.capital) }}</strong>
      </div>
      <div class="metric">
        <span>总收益</span>
        <strong :class="bot.profit >= 0 ? 'up' : 'down'">{{ formatMoney(bot.profit) }}</strong>
      </div>
      <div class="metric">
        <span>收益率</span>
        <strong :class="bot.totalReturnRate >= 0 ? 'up' : 'down'">{{ (bot.totalReturnRate * 100).toFixed(2) }}%</strong>
      </div>
    </div>

    <div class="bot-card__meta">
      <span>运行时长：{{ bot.runtime }}</span>
      <span v-if="bot.createdAt">创建于：{{ bot.createdAt.slice(0, 10) }}</span>
    </div>

    <div class="bot-card__actions">
      <button class="bot-card__action-btn" type="button" @click="emit('view-positions', bot.id)">查看持仓</button>
      <button class="bot-card__action-btn bot-card__action-btn--primary" type="button" @click="emit('view-detail', bot.id)">查看详情</button>
      <button v-if="bot.status === 'active'" class="bot-card__action-btn" type="button" @click="emit('pause', bot.id)">暂停</button>
      <button v-if="bot.status === 'paused'" class="bot-card__action-btn bot-card__action-btn--primary" type="button" @click="emit('resume', bot.id)">恢复</button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ManagedBot } from '../../types/Bot'

const props = defineProps<{ bot: ManagedBot }>()
const emit = defineEmits<{
  (e: 'view-positions', id: string): void
  (e: 'view-detail', id: string): void
  (e: 'pause', id: string): void
  (e: 'resume', id: string): void
}>()

const statusLabel = computed(() => ({
  active: '运行中',
  paused: '已暂停',
  error: '异常',
  offline: '离线',
}[props.bot.status] ?? props.bot.status))

function formatMoney(value: number) {
  return value.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY', maximumFractionDigits: 2 })
}
</script>

<style scoped>
.bot-card {
  padding: 20px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.bot-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.bot-card__name {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.bot-card__sub {
  margin: 6px 0 0;
  color: var(--color-text-muted);
}

.bot-card__badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e5e7eb;
  color: #374151;
}

.bot-card--active .bot-card__badge {
  background: #d1fae5;
  color: #065f46;
}

.bot-card--paused .bot-card__badge {
  background: #fef3c7;
  color: #92400e;
}

.bot-card--error .bot-card__badge,
.bot-card--offline .bot-card__badge {
  background: #fee2e2;
  color: #991b1b;
}

.bot-card__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.metric {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
}

.metric span {
  font-size: 12px;
  color: var(--color-text-muted);
}

.metric strong {
  font-size: 16px;
}

.up {
  color: #047857;
}

.down {
  color: #b91c1c;
}

.bot-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.bot-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.bot-card__action-btn {
  padding: 8px 14px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 10px;
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-primary);
}

.bot-card__action-btn--primary {
  border-color: #111827;
  background: #111827;
  color: #fff;
}

@media (max-width: 768px) {
  .bot-card__metrics {
    grid-template-columns: 1fr;
  }
}
</style>
