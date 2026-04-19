<template>
  <section class="metrics-panel" data-test="metrics-panel">
    <section class="report-summary">
      <div class="report-summary__hero">
        <div class="report-summary__copy">
          <div class="report-summary__meta">
            <span class="summary-chip">{{ $t('backtestReport.generatedAt') }} · {{ completedAtLabel }}</span>
            <span class="summary-chip">{{ $t('backtestReport.symbol') }} · {{ symbolLabel }}</span>
            <span class="summary-chip">{{ $t('backtestReport.timeRange') }} · {{ timeRangeLabel }}</span>
          </div>
          <h2 class="report-summary__title">{{ $t('backtestReport.reportSummary') }}</h2>
          <p class="report-summary__subtitle">{{ $t('backtestReport.reportSummarySubtitle') }}</p>
        </div>

        <div class="quality-score-card">
          <span class="quality-score-card__label">{{ $t('backtestReport.qualityScore') }}</span>
          <div class="quality-score-card__value-row">
            <strong class="quality-score-card__value">{{ qualityScore }}</strong>
            <span class="quality-score-card__unit">{{ $t('backtestReport.scoreOutOf') }}</span>
          </div>
          <span :class="['quality-score-card__tone', toneClass(qualityTone)]">{{ qualityLabel }}</span>
        </div>
      </div>

      <div class="summary-facts">
        <article v-for="fact in snapshotFacts" :key="fact.label" class="summary-fact">
          <span class="summary-fact__label">{{ fact.label }}</span>
          <strong class="summary-fact__value">{{ fact.value }}</strong>
          <span :class="['summary-fact__note', toneClass(fact.tone)]">{{ fact.note }}</span>
        </article>
      </div>

      <article class="summary-conclusion">
        <div class="summary-conclusion__header">
          <div>
            <span class="analysis-panel__eyebrow">{{ $t('backtestReport.executiveSummary') }}</span>
            <h3 class="summary-conclusion__title">{{ summaryHeadline }}</h3>
          </div>
          <span :class="['summary-conclusion__pill', toneClass(qualityTone)]">{{ qualityLabel }}</span>
        </div>
        <p class="summary-conclusion__body">{{ summaryBody }}</p>
        <div class="summary-conclusion__tags">
          <span
            v-for="tag in summaryTags"
            :key="tag.label"
            :class="['summary-conclusion__tag', toneClass(tag.tone)]"
          >
            {{ tag.label }} · {{ tag.value }}
          </span>
        </div>
      </article>

      <div v-if="aiSummary" class="ai-summary-block">
        <span class="analysis-panel__eyebrow">AI Insight</span>
        <p class="ai-summary-block__text">{{ aiSummary }}</p>
      </div>
    </section>

    <div class="metrics-grid">
      <StatCard
        v-for="metric in coreMetrics"
        :key="metric.label"
        :label="metric.label"
        :show-disclaimer="metric.showDisclaimer"
        :show-sign="metric.showSign"
        :suffix="metric.suffix"
        :value="metric.value"
        :variant="metric.variant"
      >
        <template #label-extra>
          <MetricTooltip :metric-key="metric.metricKey" />
        </template>
      </StatCard>
    </div>

    <section class="analysis-grid">
      <article class="analysis-panel" data-test="report-insights">
        <div class="analysis-panel__header">
          <span class="analysis-panel__eyebrow">{{ $t('backtestReport.keyObservationsTitle') }}</span>
          <h3 class="analysis-panel__title">{{ $t('backtestReport.reportSummary') }}</h3>
          <p class="analysis-panel__subtitle">{{ $t('backtestReport.keyObservationsSubtitle') }}</p>
        </div>
        <div class="analysis-panel__body">
          <article v-for="item in insightItems" :key="item.title" :class="['insight-row', toneClass(item.tone)]">
            <span class="insight-row__dot"></span>
            <div class="insight-row__content">
              <strong>{{ item.title }}</strong>
              <p>{{ item.body }}</p>
            </div>
          </article>
          <div v-if="diagnosisNarration" class="insight-row tone-warning">
            <span class="insight-row__dot"></span>
            <div class="insight-row__content">
              <strong>{{ $t('backtestReport.aiDiagnosis') }}</strong>
              <p>{{ diagnosisNarration }}</p>
            </div>
          </div>
        </div>
      </article>

      <article class="analysis-panel" data-test="report-diagnostics">
        <div class="analysis-panel__header">
          <span class="analysis-panel__eyebrow">{{ $t('backtestReport.diagnosticsTitle') }}</span>
          <h3 class="analysis-panel__title">{{ $t('backtestReport.qualityScore') }}</h3>
          <p class="analysis-panel__subtitle">{{ $t('backtestReport.diagnosticsSubtitle') }}</p>
        </div>
        <div class="diagnostic-grid">
          <div v-for="row in diagnosticRows" :key="row.label" class="diagnostic-row">
            <span class="diagnostic-row__label">{{ row.label }}</span>
            <strong :class="['diagnostic-row__value', toneClass(row.tone)]">{{ row.value }}</strong>
          </div>
        </div>
      </article>
    </section>

    <article v-if="anomalyAlerts && anomalyAlerts.length" class="analysis-panel analysis-panel--alerts" data-test="report-alerts">
      <div class="analysis-panel__header">
        <span class="analysis-panel__eyebrow">{{ $t('backtestReport.alertsTitle') }}</span>
        <h3 class="analysis-panel__title">{{ $t('backtestReport.alertsTitle') }}</h3>
      </div>
      <div class="analysis-panel__body">
        <div v-for="(alert, i) in anomalyAlerts" :key="i" class="insight-row tone-negative">
          <span class="insight-row__dot"></span>
          <div class="insight-row__content">
            <strong>{{ alert.title }}</strong>
            <p>{{ alert.description }}</p>
          </div>
        </div>
      </div>
    </article>

    <section class="metrics-board">
      <div class="metrics-board__header">
        <div class="metrics-board__header-main">
          <span class="analysis-panel__eyebrow">{{ $t('backtestReport.metricsCount', { count: detailedMetrics.length }) }}</span>
          <h3 class="analysis-panel__title">{{ $t('backtestReport.metricBoardTitle') }}</h3>
        </div>
        <p class="metrics-board__subtitle">{{ $t('backtestReport.metricBoardSubtitle') }}</p>
      </div>
      <div class="metrics-board__grid">
        <MetricCard
          v-for="metric in detailedMetrics"
          :key="metric.label"
          :caption="metric.caption"
          :label="metric.label"
          :metric-key="metric.metricKey"
          :tone="metric.tone"
          :value="metric.value"
        />
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import MetricTooltip from '../../../components/help/MetricTooltip.vue'
import StatCard from '../../../components/StatCard.vue'
import MetricCard from './MetricCard.vue'

type Tone = 'positive' | 'negative' | 'warning' | 'neutral'

interface MetricRow {
  label: string
  metricKey: string
  value: string
  tone: Tone
  caption: string
}

interface CoreMetric {
  label: string
  metricKey: string
  value: string
  suffix?: string
  variant: 'up' | 'down' | 'info' | 'default'
  showSign: boolean
  showDisclaimer: boolean
}

interface LabeledToneValue {
  label: string
  value: string
  tone: Tone
}

interface SnapshotFact extends LabeledToneValue {
  note: string
}

interface InsightItem {
  title: string
  body: string
  tone: Tone
}

defineProps<{
  completedAtLabel: string
  symbolLabel: string
  timeRangeLabel: string
  qualityScore: number
  qualityTone: Tone
  qualityLabel: string
  summaryHeadline: string
  summaryBody: string
  summaryTags: LabeledToneValue[]
  snapshotFacts: SnapshotFact[]
  insightItems: InsightItem[]
  diagnosticRows: LabeledToneValue[]
  coreMetrics: CoreMetric[]
  detailedMetrics: MetricRow[]
  aiSummary?: string
  diagnosisNarration?: string
  anomalyAlerts?: Array<{ title: string; description: string; severity?: string }>
}>()

function toneClass(tone: Tone): string {
  return `tone-${tone}`
}
</script>

<style scoped>
.metrics-panel {
  display: grid;
  gap: var(--spacing-xl);
}

.report-summary {
  display: grid;
  gap: var(--spacing-lg);
  padding: clamp(18px, 3vw, 28px);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.report-summary::before {
  content: "";
  position: absolute;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--color-accent);
  top: -28px;
  left: clamp(18px, 4vw, 48px);
  opacity: 0.22;
}

.report-summary::after {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  background: var(--color-danger);
  bottom: -70px;
  right: -50px;
  transform: rotate(25deg);
  border-radius: 22px;
  opacity: 0.2;
}

.report-summary__hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: var(--spacing-lg);
  position: relative;
  z-index: 1;
}

.report-summary__copy {
  display: grid;
  gap: var(--spacing-sm);
}

.report-summary__meta,
.summary-conclusion__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.summary-chip,
.summary-conclusion__pill,
.summary-conclusion__tag,
.quality-score-card__tone {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.report-summary__title,
.analysis-panel__title {
  margin: 0;
}

.report-summary__subtitle,
.summary-conclusion__body,
.analysis-panel__subtitle,
.metrics-board__subtitle,
.insight-row__content p {
  margin: 0;
  color: var(--color-text-secondary);
}

.quality-score-card {
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 18px;
  border-radius: 14px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.quality-score-card::before {
  content: "";
  position: absolute;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-primary);
  right: -12px;
  top: -12px;
  opacity: 0.9;
}

.quality-score-card__label,
.summary-fact__label,
.analysis-panel__eyebrow,
.diagnostic-row__label {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.quality-score-card__value-row,
.summary-conclusion__header,
.diagnostic-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.quality-score-card__value,
.summary-fact__value,
.diagnostic-row__value {
  font-family: 'DM Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.quality-score-card__value {
  font-size: clamp(2.1rem, 4vw, 3rem);
  line-height: 1;
}

.quality-score-card__unit {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.summary-facts,
.analysis-grid,
.metrics-grid,
.metrics-board__grid {
  display: grid;
  gap: var(--spacing-lg);
}

.summary-facts {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 2px solid var(--color-border);
  border-bottom: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.summary-fact {
  display: grid;
  gap: 4px;
  padding: 18px 20px;
  border-right: 2px solid var(--color-border-light);
}

.summary-fact:last-child {
  border-right: none;
}

.summary-conclusion {
  display: grid;
  gap: 14px;
  padding: 22px 24px;
  border-top: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.summary-conclusion__title {
  margin: 6px 0 0;
  font-size: clamp(1.15rem, 2vw, 1.55rem);
  letter-spacing: -0.03em;
}

.summary-conclusion__body {
  max-width: 900px;
  font-size: var(--font-size-lg);
  line-height: 1.7;
}

.summary-conclusion__tag {
  border-style: dashed;
  border-color: #d0d0cc;
}

.metrics-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.analysis-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.analysis-panel,
.metrics-board {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  position: relative;
}

.analysis-panel:first-child::before {
  content: "";
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-accent);
  top: -18px;
  left: -18px;
  opacity: 0.18;
}

.analysis-panel:last-child::before {
  content: "";
  position: absolute;
  width: 52px;
  height: 52px;
  border-radius: 10px;
  background: var(--color-primary);
  bottom: -16px;
  right: -16px;
  transform: rotate(20deg);
  opacity: 0.16;
}

.analysis-panel__header,
.metrics-board__header {
  display: grid;
  gap: 6px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.analysis-panel__body,
.diagnostic-grid {
  display: grid;
  gap: 0;
  padding: 4px var(--spacing-md) var(--spacing-md);
  position: relative;
  z-index: 1;
}

.insight-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 12px;
  padding: 0 var(--spacing-lg) var(--spacing-md);
}

.insight-row__dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-border);
}

.insight-row__content strong {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-primary);
}

.insight-row.tone-positive .insight-row__dot {
  background: var(--color-positive);
}

.insight-row.tone-negative .insight-row__dot {
  background: var(--color-negative);
}

.insight-row.tone-warning .insight-row__dot {
  background: var(--color-warning);
}

.diagnostic-row {
  padding: 10px var(--spacing-sm);
  border-bottom: 2px dashed var(--color-border-light);
}

.diagnostic-row:last-child {
  border-bottom: none;
}

.metrics-board__header {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.72fr);
  align-items: end;
}

.metrics-board__grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: var(--spacing-md) var(--spacing-lg) var(--spacing-lg);
}

.metrics-board__header-main {
  display: grid;
  gap: 4px;
}

.tone-positive {
  color: var(--color-positive);
}

.tone-negative {
  color: var(--color-negative);
}

.tone-warning {
  color: var(--color-warning);
}

.tone-neutral {
  color: var(--color-text-secondary);
}

.ai-summary-block {
  display: grid;
  gap: 8px;
  padding: 18px 24px;
  border-top: 2px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.ai-summary-block__text {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
  font-size: var(--font-size-md);
}

.analysis-panel--alerts .insight-row__dot {
  background: var(--color-negative);
}

@media (max-width: 900px) {
  .report-summary__hero,
  .analysis-grid,
  .metrics-board__header,
  .metrics-board__grid {
    grid-template-columns: 1fr;
  }

  .summary-facts,
  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-conclusion__header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .summary-facts,
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .summary-conclusion {
    padding: 16px;
  }
}
</style>
