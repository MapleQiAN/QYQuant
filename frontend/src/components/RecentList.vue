<template>
  <div class="recent-list card">
    <div class="list-header">
      <h3 class="list-title">{{ title }}</h3>
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
      <!-- Strategies View -->
      <template v-if="activeTab === 'strategies'">
        <div
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
                <span class="trades">{{ strategy.trades }} 笔交易</span>
              </div>
            </div>
            <div class="item-stats">
              <div :class="['returns', { positive: strategy.returns >= 0, negative: strategy.returns < 0 }]">
                {{ strategy.returns >= 0 ? '+' : '' }}{{ strategy.returns }}%
              </div>
              <ExpandIcon :class="['expand-icon', { rotated: expandedId === strategy.id }]" />
            </div>
          </div>
          
          <!-- Expanded Details -->
          <div v-if="expandedId === strategy.id" class="item-details">
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">胜率</span>
                <span class="detail-value">{{ strategy.winRate }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">最大回撤</span>
                <span class="detail-value danger">{{ strategy.maxDrawdown }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">更新时间</span>
                <span class="detail-value">{{ strategy.lastUpdate }}</span>
              </div>
            </div>
            <div class="tags-row">
              <span v-for="tag in strategy.tags" :key="tag" class="chip">{{ tag }}</span>
            </div>
            <div class="action-row">
              <button class="btn btn-secondary btn-sm">查看详情</button>
              <button class="btn btn-primary btn-sm">部署机器人</button>
            </div>
          </div>
        </div>
      </template>
      
      <!-- Robots View -->
      <template v-else>
        <div
          v-for="robot in robots"
          :key="robot.id"
          :class="['list-item', { expanded: expandedId === robot.id }]"
        >
          <div class="item-main" @click="toggleExpand(robot.id)">
            <div class="item-info">
              <div class="item-header">
                <span class="item-name">{{ robot.name }}</span>
                <span :class="['status-badge', robot.status]">
                  {{ robotStatusLabels[robot.status] }}
                </span>
              </div>
              <div class="item-meta">
                <span class="strategy-name">{{ robot.strategy }}</span>
              </div>
            </div>
            <div class="item-stats">
              <div :class="['returns', { positive: robot.profit >= 0, negative: robot.profit < 0 }]">
                {{ robot.profit >= 0 ? '+' : '' }}¥{{ robot.profit.toLocaleString() }}
              </div>
              <ExpandIcon :class="['expand-icon', { rotated: expandedId === robot.id }]" />
            </div>
          </div>
          
          <!-- Expanded Details -->
          <div v-if="expandedId === robot.id" class="item-details">
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">运行时间</span>
                <span class="detail-value">{{ robot.runtime }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">投入资金</span>
                <span class="detail-value">¥{{ robot.capital.toLocaleString() }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">收益率</span>
                <span :class="['detail-value', { success: robot.profit >= 0, danger: robot.profit < 0 }]">
                  {{ ((robot.profit / robot.capital) * 100).toFixed(2) }}%
                </span>
              </div>
            </div>
            <div class="tags-row">
              <span v-for="tag in robot.tags" :key="tag" class="chip">{{ tag }}</span>
            </div>
            <div class="action-row">
              <button class="btn btn-secondary btn-sm">查看日志</button>
              <button v-if="robot.status === 'active'" class="btn btn-warning btn-sm">暂停</button>
              <button v-else class="btn btn-primary btn-sm">启动</button>
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <div class="list-footer">
      <a href="#" class="view-all-link">
        查看全部
        <ArrowRightIcon />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { mockStrategies, mockRobots } from '../data/mockData'

interface Props {
  title?: string
}

withDefaults(defineProps<Props>(), {
  title: '最近记录'
})

const tabs = [
  { id: 'strategies', label: '策略' },
  { id: 'robots', label: '机器人' },
]

const activeTab = ref('strategies')
const expandedId = ref<string | null>(null)

const strategies = mockStrategies
const robots = mockRobots

const statusLabels: Record<string, string> = {
  running: '运行中',
  paused: '已暂停',
  stopped: '已停止',
  completed: '已完成',
}

const robotStatusLabels: Record<string, string> = {
  active: '运行中',
  paused: '已暂停',
  error: '异常',
  offline: '离线',
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

const ExpandIcon = {
  template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`
}

const ArrowRightIcon = {
  template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>`
}
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
  color: var(--color-success);
}

.returns.negative {
  color: var(--color-danger);
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
  color: var(--color-success);
}

.detail-value.danger {
  color: var(--color-danger);
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
