<template>
  <section class="ai-trust-view">
    <div class="container">
      <div class="page-header">
        <div class="header-text">
          <p class="eyebrow">{{ $t('aiTrust.eyebrow') }}</p>
          <h1 class="page-title">{{ $t('aiTrust.title') }}</h1>
          <p class="page-subtitle">{{ $t('aiTrust.subtitle') }}</p>
        </div>
        <RouterLink class="btn btn-secondary" to="/strategies/new">
          <ArrowLeftIcon />
          {{ $t('aiTrust.back') }}
        </RouterLink>
      </div>

      <!-- Core problem -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.problemTitle') }}</h2>
        <p>{{ $t('aiTrust.problemBody') }}</p>
      </section>

      <!-- Four-layer architecture -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.archTitle') }}</h2>
        <p>{{ $t('aiTrust.archIntro') }}</p>
        <div class="arch-flow">
          <div v-for="(step, i) in archSteps" :key="i" class="arch-step">
            <div class="arch-step__num">{{ i + 1 }}</div>
            <div class="arch-step__content">
              <h3>{{ $t(step.titleKey) }}</h3>
              <p>{{ $t(step.bodyKey) }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- QYIR -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.qyirTitle') }}</h2>
        <p>{{ $t('aiTrust.qyirBody') }}</p>
        <div class="highlight-grid">
          <div v-for="(hl, i) in qyirHighlights" :key="i" class="highlight-card">
            <h4>{{ $t(hl.titleKey) }}</h4>
            <p>{{ $t(hl.bodyKey) }}</p>
          </div>
        </div>
      </section>

      <!-- Verification chain -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.verifyTitle') }}</h2>
        <p>{{ $t('aiTrust.verifyIntro') }}</p>
        <div class="pipeline">
          <div v-for="(stage, i) in verifyStages" :key="i" class="pipeline-stage">
            <span class="pipeline-stage__index">{{ i + 1 }}</span>
            <span class="pipeline-stage__label">{{ $t(stage) }}</span>
            <span v-if="i < verifyStages.length - 1" class="pipeline-stage__arrow">&rarr;</span>
          </div>
        </div>
      </section>

      <!-- Rules architecture -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.rulesTitle') }}</h2>
        <p>{{ $t('aiTrust.rulesBody') }}</p>
        <div class="code-block">
          <pre><code>{{ ruleExample }}</code></pre>
        </div>
      </section>

      <!-- Profile mechanism -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.profileTitle') }}</h2>
        <p>{{ $t('aiTrust.profileBody') }}</p>
      </section>

      <!-- Human-AI collaboration -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.collabTitle') }}</h2>
        <p>{{ $t('aiTrust.collabBody') }}</p>
        <ul class="trust-list">
          <li v-for="(item, i) in collabItems" :key="i">{{ $t(item) }}</li>
        </ul>
      </section>

      <!-- Evaluation protocol -->
      <section class="trust-section">
        <h2>{{ $t('aiTrust.evalTitle') }}</h2>
        <p>{{ $t('aiTrust.evalBody') }}</p>
        <div class="eval-grid">
          <div v-for="(axis, i) in evalAxes" :key="i" class="eval-card">
            <h4>{{ $t(axis.titleKey) }}</h4>
            <p>{{ $t(axis.bodyKey) }}</p>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="trust-cta">
        <h2>{{ $t('aiTrust.ctaTitle') }}</h2>
        <p>{{ $t('aiTrust.ctaBody') }}</p>
        <RouterLink class="btn btn-primary" to="/strategies/new">
          {{ $t('aiTrust.ctaAction') }}
        </RouterLink>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { RouterLink } from 'vue-router'

const ArrowLeftIcon = () => h('svg', {
  width: 16, height: 16, viewBox: '0 0 24 24',
  fill: 'none', stroke: 'currentColor', 'stroke-width': 2,
  'stroke-linecap': 'round', 'stroke-linejoin': 'round',
}, [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'm12 19-7-7 7-7' }),
])

const archSteps = [
  { titleKey: 'aiTrust.archStep1Title', bodyKey: 'aiTrust.archStep1Body' },
  { titleKey: 'aiTrust.archStep2Title', bodyKey: 'aiTrust.archStep2Body' },
  { titleKey: 'aiTrust.archStep3Title', bodyKey: 'aiTrust.archStep3Body' },
  { titleKey: 'aiTrust.archStep4Title', bodyKey: 'aiTrust.archStep4Body' },
]

const qyirHighlights = [
  { titleKey: 'aiTrust.qyirHl1Title', bodyKey: 'aiTrust.qyirHl1Body' },
  { titleKey: 'aiTrust.qyirHl2Title', bodyKey: 'aiTrust.qyirHl2Body' },
  { titleKey: 'aiTrust.qyirHl3Title', bodyKey: 'aiTrust.qyirHl3Body' },
  { titleKey: 'aiTrust.qyirHl4Title', bodyKey: 'aiTrust.qyirHl4Body' },
]

const verifyStages = [
  'aiTrust.verifySyntax',
  'aiTrust.verifySemantic',
  'aiTrust.verifyProfile',
  'aiTrust.verifyCompile',
  'aiTrust.verifyBehavior',
]

const collabItems = [
  'aiTrust.collabItem1',
  'aiTrust.collabItem2',
  'aiTrust.collabItem3',
  'aiTrust.collabItem4',
]

const evalAxes = [
  { titleKey: 'aiTrust.evalAxis1Title', bodyKey: 'aiTrust.evalAxis1Body' },
  { titleKey: 'aiTrust.evalAxis2Title', bodyKey: 'aiTrust.evalAxis2Body' },
  { titleKey: 'aiTrust.evalAxis3Title', bodyKey: 'aiTrust.evalAxis3Body' },
  { titleKey: 'aiTrust.evalAxis4Title', bodyKey: 'aiTrust.evalAxis4Body' },
]

const ruleExample = `{
  "id": "stop_loss",
  "label": "止损",
  "when": "price < entry_price * (1 - param.stop_pct)",
  "then": { "side": "sell", "sizing": { "type": "all" } },
  "priority": 30
}`
</script>

<style scoped>
.ai-trust-view {
  width: 100%;
}

.container {
  max-width: 820px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  margin: 0;
}

.eyebrow {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0;
}

.trust-section {
  margin-bottom: var(--spacing-xl);
}

.trust-section h2 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm);
}

.trust-section > p {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
}

/* Architecture flow */
.arch-flow {
  display: grid;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.arch-step {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
}

.arch-step__num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-accent);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--font-size-sm);
  flex-shrink: 0;
}

.arch-step__content h3 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
}

.arch-step__content p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Highlight grid */
.highlight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.highlight-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
}

.highlight-card h4 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-accent);
}

.highlight-card p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Pipeline */
.pipeline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
}

.pipeline-stage {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.pipeline-stage__index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(64, 162, 255, 0.15);
  color: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: 700;
  flex-shrink: 0;
}

.pipeline-stage__label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.pipeline-stage__arrow {
  color: var(--color-text-muted);
  font-size: var(--font-size-lg);
}

/* Code block */
.code-block {
  margin-top: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: rgba(7, 17, 27, 0.94);
  padding: var(--spacing-md);
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
}

.code-block code {
  color: #f8fbff;
  font-family: var(--font-mono, 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

/* Trust list */
.trust-list {
  margin: var(--spacing-md) 0 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.trust-list li {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Eval grid */
.eval-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.eval-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
}

.eval-card h4 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-accent);
}

.eval-card p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* CTA */
.trust-cta {
  text-align: center;
  padding: var(--spacing-xl) 0;
  border-top: 1px solid var(--color-border);
}

.trust-cta h2 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm);
}

.trust-cta p {
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  margin: 0 0 var(--spacing-lg);
}

@media (max-width: 720px) {
  .page-header {
    flex-direction: column;
  }

  .highlight-grid,
  .eval-grid {
    grid-template-columns: 1fr;
  }
}
</style>
