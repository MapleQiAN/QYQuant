<template>
  <div class="strategy-report">
    <div v-if="metadata.logicExplanation" class="report-section">
      <h3 class="report-section__title">{{ $t('strategyPreview.logicTitle') }}</h3>
      <p class="report-section__body">{{ metadata.logicExplanation }}</p>
    </div>

    <div v-if="metadata.riskRules" class="report-section">
      <h3 class="report-section__title">{{ $t('strategyPreview.riskRulesTitle') }}</h3>
      <p class="report-section__body">{{ metadata.riskRules }}</p>
    </div>

    <div class="report-meta">
      <div v-if="metadata.suitableMarket" class="report-meta__item">
        <span class="report-meta__label">{{ $t('strategyPreview.suitableMarket') }}</span>
        <span class="report-meta__value">{{ metadata.suitableMarket }}</span>
      </div>
      <div v-if="metadata.riskLevel" class="report-meta__item">
        <span class="report-meta__label">{{ $t('strategyPreview.riskLevel') }}</span>
        <span class="report-meta__value" :class="`risk-badge risk-badge--${metadata.riskLevel}`">
          {{ riskLevelLabel(metadata.riskLevel) }}
        </span>
      </div>
      <div v-if="metadata.timeframe" class="report-meta__item">
        <span class="report-meta__label">{{ $t('strategyPreview.timeframe') }}</span>
        <span class="report-meta__value">{{ metadata.timeframe }}</span>
      </div>
      <div v-if="metadata.category" class="report-meta__item">
        <span class="report-meta__label">{{ $t('strategyPreview.category') }}</span>
        <span class="report-meta__value">{{ categoryLabel(metadata.category) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { AiStrategyMetadata } from '../../types/Strategy'

const { t } = useI18n()

defineProps<{
  metadata: AiStrategyMetadata
}>()

function riskLevelLabel(level: string): string {
  const map: Record<string, string> = {
    low: t('strategyPreview.riskLow'),
    medium: t('strategyPreview.riskMedium'),
    high: t('strategyPreview.riskHigh'),
  }
  return map[level] || level
}

function categoryLabel(category: string): string {
  const map: Record<string, string> = {
    'trend-following': t('strategyPreview.catTrendFollowing'),
    'mean-reversion': t('strategyPreview.catMeanReversion'),
    'momentum': t('strategyPreview.catMomentum'),
    'multi-indicator': t('strategyPreview.catMultiIndicator'),
    'other': t('strategyPreview.catOther'),
  }
  return map[category] || category
}
</script>

<style scoped>
.strategy-report {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.report-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.report-section__title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
}

.report-section__body {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.report-meta__item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
}

.report-meta__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.report-meta__value {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.risk-badge {
  text-transform: capitalize;
}

.risk-badge--low {
  color: #2a9d65;
}

.risk-badge--medium {
  color: #c87a00;
}

.risk-badge--high {
  color: #cf4e4e;
}
</style>
