<template>
  <div class="backtest-card card">
    <div class="card-header">
      <div class="header-left">
        <h3 class="card-title">回测概览</h3>
        <span class="badge badge-success">已完成</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary">
          <RefreshIcon />
          重新运行
        </button>
        <button class="btn btn-primary">
          <ExportIcon />
          导出报告
        </button>
      </div>
    </div>
    
    <!-- KPI Grid -->
    <div class="kpi-grid">
      <StatCard
        label="总收益率"
        :value="kpis.totalReturn"
        suffix="%"
        :change="kpis.totalReturn"
        :showSign="true"
        variant="success"
      >
        <template #icon>
          <TrendUpIcon />
        </template>
      </StatCard>
      
      <StatCard
        label="年化收益"
        :value="kpis.annualizedReturn"
        suffix="%"
        variant="info"
      >
        <template #icon>
          <CalendarIcon />
        </template>
      </StatCard>
      
      <StatCard
        label="夏普比率"
        :value="kpis.sharpeRatio"
        variant="default"
      >
        <template #icon>
          <TargetIcon />
        </template>
      </StatCard>
      
      <StatCard
        label="最大回撤"
        :value="kpis.maxDrawdown"
        suffix="%"
        :showSign="true"
        variant="danger"
      >
        <template #icon>
          <TrendDownIcon />
        </template>
      </StatCard>
    </div>
    
    <!-- Chart Section -->
    <div class="chart-section">
      <KlinePlaceholder
        :data="klineData"
        symbol="XAUUSD"
        timeframe="15m"
      />
    </div>
    
    <!-- Secondary Stats -->
    <div class="secondary-stats">
      <div class="stat-item">
        <span class="stat-label">胜率</span>
        <span class="stat-value">{{ kpis.winRate }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">盈亏比</span>
        <span class="stat-value">{{ kpis.profitFactor }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总交易次数</span>
        <span class="stat-value">{{ kpis.totalTrades }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均持仓天数</span>
        <span class="stat-value">{{ kpis.avgHoldingDays }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import KlinePlaceholder from './KlinePlaceholder.vue'
import StatCard from './StatCard.vue'
import { backtestKPIs, mockKlineData } from '../data/mockData'

const kpis = backtestKPIs
const klineData = mockKlineData

// Icon components
const RefreshIcon = {
  template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>`
}

const ExportIcon = {
  template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`
}

const TrendUpIcon = {
  template: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`
}

const TrendDownIcon = {
  template: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>`
}

const CalendarIcon = {
  template: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`
}

const TargetIcon = {
  template: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`
}
</script>

<style scoped>
.backtest-card {
  padding: var(--spacing-lg);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.chart-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.secondary-stats {
  display: flex;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-item .stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.stat-item .stat-value {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

@media (max-width: 1024px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .secondary-stats {
    flex-wrap: wrap;
  }
}
</style>
