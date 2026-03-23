<template>
  <article class="bot-card" :class="`bot-card--${bot.status}`">
    <div class="bot-card__header">
      <span class="bot-card__name">{{ bot.strategy_name }}</span>
      <span class="bot-card__badge">{{ statusLabel }}</span>
    </div>
    <div class="bot-card__body">
      <p class="bot-card__meta">初始资金：¥ {{ formattedCapital }}</p>
      <p class="bot-card__meta">创建时间：{{ formattedDate }}</p>
    </div>
    <div class="bot-card__actions">
      <button
        class="bot-card__action-btn"
        type="button"
        @click="emit('view-positions', bot.id)"
      >
        查看持仓
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SimulationBot } from '../../types/Simulation'

const props = defineProps<{ bot: SimulationBot }>()
const emit = defineEmits<{ (e: 'view-positions', id: string): void }>()

const STATUS_LABELS: Record<string, string> = {
  active: '运行中',
  paused: '已暂停',
  stopped: '已停止',
}

const statusLabel = computed(() => STATUS_LABELS[props.bot.status] ?? props.bot.status)

const formattedCapital = computed(() =>
  Number(props.bot.initial_capital).toLocaleString('zh-CN')
)

const formattedDate = computed(() => props.bot.created_at.slice(0, 10))
</script>

<style scoped>
.bot-card {
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
}

.bot-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.bot-card__name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.bot-card__badge {
  font-size: 12px;
  padding: 2px 8px;
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

.bot-card--stopped .bot-card__badge {
  background: #fee2e2;
  color: #991b1b;
}

.bot-card__body {
  margin-bottom: 12px;
}

.bot-card__meta {
  margin: 0 0 4px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.bot-card__actions {
  display: flex;
  gap: 8px;
}

.bot-card__action-btn {
  padding: 6px 14px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 8px;
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-primary);
}

.bot-card__action-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}
</style>
