<template>
  <div class="recent-list card">
    <div class="list-header">
      <h3 class="list-title">{{ resolvedTitle }}</h3>
      <div class="tab-switcher">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div class="list-content">
      <template v-if="activeTab === 'strategies'">
        <SkeletonState v-if="strategiesLoading" :lines="6" />
        <ErrorState
          v-else-if="strategiesError"
          :message="strategiesError"
          :action-label="$t('common.retry')"
          @retry="$emit('retry-strategies')"
        />
        <EmptyState v-else-if="!strategies.length" />
        <div
          v-else
          v-for="strategy in strategies"
          :key="strategy.id"
          :class="['list-item', { expanded: expandedId === strategy.id }]"
        >
          <div class="item-main" @click="toggleExpand(strategy.id)">
            <div class="item-info">
              <div class="item-header">
                <span class="item-name">{{ strategy.name }}</span>
                <span :class="['status-badge', strategy.status]">
                  {{ statusLabels[strategy.status] }}
                </span>
              </div>
              <div class="item-meta">
                <span class="symbol">{{ strategy.symbol }}</span>
                <span class="separator">·</span>
                <span class="trades">{{ strategy.trades }} {{ $t('recent.trades') }}</span>
              </div>
            </div>
            <div class="item-stats">
              <div :class="['returns', { positive: strategy.returns >= 0, negative: strategy.returns < 0 }]">
                {{ strategy.returns >= 0 ? '+' : '' }}{{ strategy.returns }}%
              </div>
              <ExpandIcon :class="['expand-icon', { rotated: expandedId === strategy.id }]" />
            </div>
          </div>

          <div v-if="expandedId === strategy.id" class="item-details">
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.winRate') }}</span>
                <span class="detail-value">{{ strategy.winRate }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.maxDrawdown') }}</span>
                <span class="detail-value danger">{{ strategy.maxDrawdown }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.updatedAt') }}</span>
                <span class="detail-value">{{ strategy.lastUpdate }}</span>
              </div>
            </div>
            <div class="tags-row">
              <span v-for="tag in strategy.tags" :key="tag" class="chip">{{ tag }}</span>
            </div>
            <div class="action-row">
              <button class="btn btn-secondary btn-sm">{{ $t('recent.viewDetails') }}</button>
              <button class="btn btn-primary btn-sm">{{ $t('recent.deployBot') }}</button>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <SkeletonState v-if="botsLoading" :lines="6" />
        <ErrorState
          v-else-if="botsError"
          :message="botsError"
          :action-label="$t('common.retry')"
          @retry="$emit('retry-bots')"
        />
        <EmptyState v-else-if="!bots.length" />
        <div
          v-else
          v-for="bot in bots"
          :key="bot.id"
          :class="['list-item', { expanded: expandedId === bot.id }]"
        >
          <div class="item-main" @click="toggleExpand(bot.id)">
            <div class="item-info">
              <div class="item-header">
                <span class="item-name">{{ bot.name }}</span>
                <span :class="['status-badge', bot.status]">
                  {{ robotStatusLabels[bot.status] }}
                </span>
              </div>
              <div class="item-meta">
                <span class="strategy-name">{{ bot.strategy }}</span>
              </div>
            </div>
            <div class="item-stats">
              <div :class="['returns', { positive: bot.profit >= 0, negative: bot.profit < 0 }]">
                {{ bot.profit >= 0 ? '+' : '' }}{{ formatCurrency(bot.profit) }}
              </div>
              <ExpandIcon :class="['expand-icon', { rotated: expandedId === bot.id }]" />
            </div>
          </div>

          <div v-if="expandedId === bot.id" class="item-details">
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.runtime') }}</span>
                <span class="detail-value">{{ bot.runtime }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.capital') }}</span>
                <span class="detail-value">{{ formatCurrency(bot.capital) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ $t('recent.roi') }}</span>
                <span :class="['detail-value', { success: bot.profit >= 0, danger: bot.profit < 0 }]">
                  {{ ((bot.profit / bot.capital) * 100).toFixed(2) }}%
                </span>
              </div>
            </div>
            <div class="tags-row">
              <span v-for="tag in bot.tags" :key="tag" class="chip">{{ tag }}</span>
            </div>
            <div class="action-row">
              <button class="btn btn-secondary btn-sm">{{ $t('recent.viewLogs') }}</button>
              <button v-if="bot.status === 'active'" class="btn btn-warning btn-sm">
                {{ $t('recent.pause') }}
              </button>
              <button v-else class="btn btn-primary btn-sm">
                {{ $t('recent.start') }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="list-footer">
      <a href="#" class="view-all-link">
        {{ $t('common.viewAll') }}
        <ArrowRightIcon />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Bot } from '../types/Bot'
import type { Strategy } from '../types/Strategy'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'
import SkeletonState from './SkeletonState.vue'

const props = withDefaults(defineProps<{
  title?: string
  strategies?: Strategy[]
  strategiesLoading?: boolean
  strategiesError?: string | null
  bots?: Bot[]
  botsLoading?: boolean
  botsError?: string | null
}>(), {
  strategies: () => [],
  strategiesLoading: false,
  strategiesError: null,
  bots: () => [],
  botsLoading: false,
  botsError: null
})

defineEmits<{
  (event: 'retry-strategies'): void
  (event: 'retry-bots'): void
}>()

const { t, locale } = useI18n()

const activeTab = ref<'strategies' | 'bots'>('strategies')
const expandedId = ref<string | null>(null)

const tabs = computed(() => [
  { id: 'strategies', label: t('recent.tabs.strategies') },
  { id: 'bots', label: t('recent.tabs.bots') }
])

const resolvedTitle = computed(() => props.title || t('dashboard.recentTitle'))

const statusLabels = computed<Record<string, string>>(() => ({
  draft: t('status.draft'),
  running: t('status.running'),
  paused: t('status.paused'),
  stopped: t('status.stopped'),
  completed: t('status.completed')
}))

const robotStatusLabels = computed<Record<string, string>>(() => ({
  active: t('status.active'),
  paused: t('status.paused'),
  error: t('status.error'),
  offline: t('status.offline')
}))

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function formatCurrency(value: number) {
  const localeValue = locale.value === 'zh' ? 'zh-CN' : 'en-US'
  return value.toLocaleString(localeValue, { minimumFractionDigits: 0 })
}

const ExpandIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('polyline', { points: '6 9 12 15 18 9' })
])

const ArrowRightIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M5 12h14' }),
  h('path', { d: 'm12 5 7 7-7 7' })
])
</script>

<style scoped>
.recent-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.list-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.tab-switcher {
  display: flex;
  background: var(--color-background);
  border-radius: var(--radius-md);
  padding: var(--spacing-xs);
}

.tab-btn {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  background: var(--color-surface);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.list-item {
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.list-item:hover {
  background: var(--color-background);
}

.list-item.expanded {
  background: var(--color-background);
}

.item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  cursor: pointer;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.item-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.status-badge.running,
.status-badge.active {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.paused {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-badge.stopped,
.status-badge.draft,
.status-badge.offline {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}

.status-badge.completed {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.status-badge.error {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.separator {
  color: var(--color-border);
}

.item-stats {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.returns {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.returns.positive {
  color: var(--color-up);
}

.returns.negative {
  color: var(--color-down);
}

.expand-icon {
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.item-details {
  padding: 0 var(--spacing-md) var(--spacing-md);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.detail-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.detail-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.detail-value.success {
  color: var(--color-up);
}

.detail-value.danger {
  color: var(--color-down);
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.action-row {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-xs);
}

.btn-warning {
  background: var(--color-warning);
  color: var(--color-text-inverse);
}

.btn-warning:hover {
  background: #d97706;
}

.list-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.view-all-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  text-decoration: none;
}

.view-all-link:hover {
  color: var(--color-primary-dark);
}
</style>
