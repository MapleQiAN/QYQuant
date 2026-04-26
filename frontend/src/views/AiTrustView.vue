<template>
  <section class="ai-trust-view fade-in">
    <div class="trust-shell">
    <!-- Hero -->
    <header class="hero card">
      <div class="hero-inner">
        <div class="hero-nav">
          <RouterLink class="back-link" to="/strategies/new">
            <ArrowLeftIcon />
            <span>{{ $t('aiTrust.back') }}</span>
          </RouterLink>
        </div>
        <div class="hero-body">
          <span class="eyebrow-badge">{{ $t('aiTrust.eyebrow') }}</span>
          <h1 class="hero-title">{{ $t('aiTrust.title') }}</h1>
          <p class="hero-subtitle">{{ $t('aiTrust.subtitle') }}</p>
        </div>
      </div>
    </header>

    <div class="trust-content">
      <!-- Core problem -->
      <section class="section-block problem-block">
        <div class="section-label-bar">
          <span class="section-index">01</span>
          <h2 class="section-heading">{{ $t('aiTrust.problemTitle') }}</h2>
        </div>
        <p class="section-body-lg">{{ $t('aiTrust.problemBody') }}</p>
      </section>

      <!-- Four-layer architecture -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">02</span>
          <h2 class="section-heading">{{ $t('aiTrust.archTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.archIntro') }}</p>
        <div class="arch-timeline stagger-in">
          <div v-for="(step, i) in archSteps" :key="i" class="arch-step">
            <div class="arch-step__rail">
              <div class="arch-step__marker">{{ i + 1 }}</div>
              <div v-if="i < archSteps.length - 1" class="arch-step__line" />
            </div>
            <div class="arch-step__card">
              <h3 class="arch-step__title">{{ $t(step.titleKey) }}</h3>
              <p class="arch-step__body">{{ $t(step.bodyKey) }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- QYIR -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">03</span>
          <h2 class="section-heading">{{ $t('aiTrust.qyirTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.qyirBody') }}</p>
        <div class="feature-grid stagger-in">
          <div v-for="(hl, i) in qyirHighlights" :key="i" class="feature-card">
            <span class="feature-card__num">{{ String(i + 1).padStart(2, '0') }}</span>
            <h4 class="feature-card__title">{{ $t(hl.titleKey) }}</h4>
            <p class="feature-card__body">{{ $t(hl.bodyKey) }}</p>
          </div>
        </div>
      </section>

      <!-- Verification pipeline -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">04</span>
          <h2 class="section-heading">{{ $t('aiTrust.verifyTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.verifyIntro') }}</p>
        <div class="pipeline-track stagger-in">
          <div v-for="(stage, i) in verifyStages" :key="i" class="pipeline-node">
            <div class="pipeline-node__dot">
              <span class="pipeline-node__num">{{ i + 1 }}</span>
            </div>
            <span class="pipeline-node__label">{{ $t(stage) }}</span>
            <div v-if="i < verifyStages.length - 1" class="pipeline-node__connector">
              <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
                <path d="M0 6h20m0 0l-4-4m4 4l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      <!-- Rules + Profile (combined card) -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">05</span>
          <h2 class="section-heading">{{ $t('aiTrust.rulesTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.rulesBody') }}</p>
        <div class="code-surface">
          <div class="code-header">
            <span class="code-dots">
              <i /><i /><i />
            </span>
            <span class="code-filename">rule-stop_loss.qyir.json</span>
          </div>
          <pre class="code-body"><code>{{ ruleExample }}</code></pre>
        </div>
      </section>

      <!-- Profile mechanism -->
      <section class="section-block profile-block">
        <div class="section-label-bar">
          <span class="section-index">06</span>
          <h2 class="section-heading">{{ $t('aiTrust.profileTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.profileBody') }}</p>
      </section>

      <!-- Human-AI collaboration -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">07</span>
          <h2 class="section-heading">{{ $t('aiTrust.collabTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.collabBody') }}</p>
        <div class="collab-list stagger-in">
          <div v-for="(item, i) in collabItems" :key="i" class="collab-item">
            <span class="collab-item__marker">{{ i + 1 }}</span>
            <p class="collab-item__text">{{ $t(item) }}</p>
          </div>
        </div>
      </section>

      <!-- Evaluation protocol -->
      <section class="section-block">
        <div class="section-label-bar">
          <span class="section-index">08</span>
          <h2 class="section-heading">{{ $t('aiTrust.evalTitle') }}</h2>
        </div>
        <p class="section-body">{{ $t('aiTrust.evalBody') }}</p>
        <div class="eval-grid stagger-in">
          <div v-for="(axis, i) in evalAxes" :key="i" class="eval-card">
            <span class="eval-card__axis">Axis {{ i + 1 }}</span>
            <h4 class="eval-card__title">{{ $t(axis.titleKey) }}</h4>
            <p class="eval-card__body">{{ $t(axis.bodyKey) }}</p>
          </div>
        </div>
      </section>
    </div>

      <!-- CTA -->
      <section class="cta-card card">
        <div class="cta-inner">
          <h2 class="cta-title">{{ $t('aiTrust.ctaTitle') }}</h2>
          <p class="cta-body">{{ $t('aiTrust.ctaBody') }}</p>
          <RouterLink class="btn btn-primary cta-btn" to="/strategies/new">
            {{ $t('aiTrust.ctaAction') }}
            <ArrowRightIcon />
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { RouterLink } from 'vue-router'

const ArrowLeftIcon = () => h('svg', {
  width: 14, height: 14, viewBox: '0 0 24 24',
  fill: 'none', stroke: 'currentColor', 'stroke-width': 2.5,
  'stroke-linecap': 'round', 'stroke-linejoin': 'round',
}, [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'm12 19-7-7 7-7' }),
])

const ArrowRightIcon = () => h('svg', {
  width: 16, height: 16, viewBox: '0 0 24 24',
  fill: 'none', stroke: 'currentColor', 'stroke-width': 2.5,
  'stroke-linecap': 'round', 'stroke-linejoin': 'round',
}, [
  h('path', { d: 'M5 12h14' }),
  h('path', { d: 'm12 5 7 7-7 7' }),
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
/* ── Layout Shell ── */
.ai-trust-view {
  width: 100%;
}

.trust-shell {
  max-width: 920px;
  margin: 0 auto;
  padding: var(--spacing-lg);
  display: grid;
  gap: var(--spacing-lg);
}

/* ── Hero ── */
.hero {
  overflow: hidden;
}

.hero-inner {
  padding: clamp(24px, 3vw, 40px);
  display: grid;
  gap: var(--spacing-lg);
}

.hero-nav {
  display: flex;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1.5px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.back-link:hover {
  border-color: var(--color-primary-border);
  color: var(--color-primary);
  background: var(--color-primary-bg);
}

.hero-body {
  display: grid;
  gap: 12px;
  max-width: 72ch;
}

.eyebrow-badge {
  display: inline-flex;
  width: fit-content;
  padding: 5px 12px;
  border-radius: var(--radius-full);
  border: 1.5px solid var(--color-primary-border);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: clamp(11px, 0.85vw, 13px);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.hero-title {
  font-size: clamp(28px, 3.2vw, 48px);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.035em;
  color: var(--color-text-primary);
}

.hero-subtitle {
  font-size: clamp(14px, 1.1vw, 17px);
  line-height: 1.6;
  color: var(--color-text-secondary);
  max-width: 64ch;
}

/* ── Section Blocks ── */
.trust-content {
  display: grid;
  gap: var(--spacing-xl);
}

.section-block {
  display: grid;
  gap: var(--spacing-md);
}

.section-label-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  font-family: var(--font-mono);
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.section-heading {
  font-size: clamp(20px, 1.6vw, 26px);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  margin: 0;
}

.section-body {
  color: var(--color-text-secondary);
  line-height: 1.7;
  max-width: 72ch;
}

.section-body-lg {
  color: var(--color-text-secondary);
  font-size: clamp(14px, 1.05vw, 16px);
  line-height: 1.75;
  max-width: 72ch;
  padding: var(--spacing-md) var(--spacing-lg);
  border-left: 3px solid var(--color-accent);
  background: var(--color-accent-bg);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

/* ── Problem Block ── */
.problem-block {
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--color-border-light);
}

/* ── Architecture Timeline ── */
.arch-timeline {
  display: grid;
  gap: 0;
  margin-top: var(--spacing-sm);
}

.arch-step {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: var(--spacing-md);
}

.arch-step__rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.arch-step__marker {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-accent);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: var(--font-size-sm);
  flex-shrink: 0;
  box-shadow: 0 0 0 4px var(--color-surface);
}

.arch-step__line {
  width: 2px;
  flex: 1;
  min-height: 16px;
  background: var(--color-border-light);
  margin: 4px 0;
}

.arch-step__card {
  padding: var(--spacing-md);
  padding-left: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.arch-step__title {
  font-size: clamp(15px, 1.1vw, 18px);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 6px;
  letter-spacing: -0.01em;
}

.arch-step__body {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.65;
  margin: 0;
}

/* ── Feature Grid (QYIR) ── */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
}

.feature-card {
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color var(--transition-fast), transform var(--transition-fast);
}

.feature-card:hover {
  border-color: var(--color-primary-border);
  transform: translateY(-2px);
}

.feature-card__num {
  font-family: var(--font-mono);
  font-size: clamp(28px, 2.5vw, 40px);
  font-weight: 800;
  color: var(--color-accent);
  line-height: 1;
  letter-spacing: -0.04em;
  opacity: 0.6;
}

.feature-card__title {
  font-size: clamp(14px, 1vw, 16px);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.feature-card__body {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ── Pipeline Track ── */
.pipeline-track {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0;
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.pipeline-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pipeline-node__dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--color-primary);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pipeline-node__num {
  font-size: 10px;
  font-weight: 800;
  color: var(--color-primary);
  font-family: var(--font-mono);
}

.pipeline-node__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
}

.pipeline-node__connector {
  color: var(--color-border);
  margin: 0 6px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* ── Code Surface ── */
.code-surface {
  margin-top: var(--spacing-sm);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: #111111;
  overflow: hidden;
}

.code-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.code-dots {
  display: flex;
  gap: 6px;
}

.code-dots i {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.code-dots i:nth-child(1) { background: #ff5f57; }
.code-dots i:nth-child(2) { background: #febc2e; }
.code-dots i:nth-child(3) { background: #28c840; }

.code-filename {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.35);
  font-family: var(--font-mono);
}

.code-body {
  margin: 0;
  padding: var(--spacing-lg);
  overflow-x: auto;
}

.code-body code {
  color: #e8ecf1;
  font-family: var(--font-mono);
  font-size: clamp(12px, 0.9vw, 14px);
  line-height: 1.75;
}

/* ── Profile Block ── */
.profile-block {
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--color-border-light);
}

/* ── Collab List ── */
.collab-list {
  display: grid;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.collab-item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  align-items: start;
  transition: border-color var(--transition-fast);
}

.collab-item:hover {
  border-color: var(--color-primary-border);
}

.collab-item__marker {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-bg);
  color: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
}

.collab-item__text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.65;
  margin: 0;
}

/* ── Eval Grid ── */
.eval-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
}

.eval-card {
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color var(--transition-fast), transform var(--transition-fast);
}

.eval-card:hover {
  border-color: var(--color-primary-border);
  transform: translateY(-2px);
}

.eval-card__axis {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  font-family: var(--font-mono);
}

.eval-card__title {
  font-size: clamp(14px, 1vw, 16px);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.eval-card__body {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ── CTA ── */
.cta-card {
  text-align: center;
}

.cta-inner {
  padding: clamp(32px, 4vw, 56px);
  display: grid;
  gap: var(--spacing-md);
  justify-items: center;
}

.cta-title {
  font-size: clamp(22px, 2vw, 32px);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  margin: 0;
}

.cta-body {
  color: var(--color-text-secondary);
  max-width: 52ch;
  line-height: 1.6;
  margin: 0;
}

.cta-btn {
  margin-top: var(--spacing-sm);
  padding: 12px 28px;
  font-size: var(--font-size-lg);
}

/* ── Responsive ── */
@media (max-width: 720px) {
  .feature-grid,
  .eval-grid {
    grid-template-columns: 1fr;
  }

  .pipeline-track {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }

  .pipeline-node__connector {
    transform: rotate(90deg);
    margin: 2px 0;
  }

  .arch-step {
    grid-template-columns: 40px minmax(0, 1fr);
  }
}
</style>
