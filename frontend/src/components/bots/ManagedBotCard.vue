<template>
  <article class="bot-card" :class="`bot-card--${bot.status}`">
    <!-- Status Accent Bar -->
    <div class="bot-card__accent"></div>

    <div class="bot-card__header">
      <div class="bot-card__header-left">
        <span class="bot-card__name">{{ bot.name }}</span>
        <p class="bot-card__sub">
          <span class="meta-pill">{{ bot.strategyName }}</span>
          <span class="meta-divider">·</span>
          <span class="meta-item">{{ bot.integrationDisplayName }}</span>
        </p>
      </div>
      <span class="bot-card__badge">
        <span class="bot-card__badge-dot"></span>
        {{ statusLabel }}
      </span>
    </div>

    <div class="bot-card__metrics">
      <div class="metric">
        <span class="metric__label">托管金额</span>
        <strong class="metric__value tnum">{{ formatMoney(bot.capital) }}</strong>
      </div>
      <div class="metric">
        <span class="metric__label">总收益</span>
        <strong class="metric__value tnum" :class="bot.profit >= 0 ? 'positive' : 'negative'">{{ formatMoney(bot.profit) }}</strong>
      </div>
      <div class="metric">
        <span class="metric__label">收益率</span>
        <strong class="metric__value tnum" :class="bot.totalReturnRate >= 0 ? 'positive' : 'negative'">{{ (bot.totalReturnRate * 100).toFixed(2) }}%</strong>
      </div>
    </div>

    <div class="bot-card__meta">
      <span class="meta-item">运行时长：{{ bot.runtime }}</span>
      <span v-if="bot.createdAt" class="meta-item">创建于：{{ bot.createdAt.slice(0, 10) }}</span>
    </div>

    <div class="bot-card__actions">
      <button class="btn btn-secondary btn--sm" type="button" @click="emit('view-positions', bot.id)">查看持仓</button>
      <button class="btn btn-primary btn--sm" type="button" @click="emit('view-detail', bot.id)">查看详情</button>
      <button v-if="bot.status === 'active'" class="btn btn-secondary btn--sm" type="button" @click="emit('pause', bot.id)">暂停</button>
      <button v-if="bot.status === 'paused'" class="btn btn-primary btn--sm" type="button" @click="emit('resume', bot.id)">恢复</button>
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
/* ── Bot Card — Bauhaus ── */
.bot-card {
  position: relative;
  padding: 20px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.bot-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-lg);
}

/* Status accent bar — bottom edge */
.bot-card__accent {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color-text-muted);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.bot-card--active .bot-card__accent {
  background: var(--color-success);
}

.bot-card--paused .bot-card__accent {
  background: var(--color-warning);
}

.bot-card--error .bot-card__accent,
.bot-card--offline .bot-card__accent {
  background: var(--color-danger);
}

/* ── Header ── */
.bot-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.bot-card__name {
  display: block;
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.bot-card__sub {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 6px 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.meta-divider {
  color: var(--color-border-strong);
}

.meta-item {
  color: var(--color-text-muted);
}

/* ── Status Badge ── */
.bot-card__badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  white-space: nowrap;
  border: 2px solid transparent;
  background: var(--color-surface-active);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.bot-card__badge-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.bot-card--active .bot-card__badge {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: rgba(46, 125, 50, 0.25);
}

.bot-card--paused .bot-card__badge {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border-color: rgba(230, 81, 0, 0.25);
}

.bot-card--error .bot-card__badge,
.bot-card--offline .bot-card__badge {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border-color: rgba(212, 57, 59, 0.25);
}

/* ── Metrics Grid ── */
.bot-card__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.metric {
  display: grid;
  gap: 6px;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-background);
  border: 1px solid var(--color-border-light);
}

.metric__label {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.metric__value {
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.metric__value.positive {
  color: var(--color-positive);
}

.metric__value.negative {
  color: var(--color-negative);
}

/* ── Meta Row ── */
.bot-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* ── Actions ── */
.bot-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.btn--sm {
  padding: 5px 12px;
  font-size: var(--font-size-xs);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .bot-card__metrics {
    grid-template-columns: 1fr;
  }

  .bot-card__header {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
</style>
