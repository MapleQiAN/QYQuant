<template>
  <div class="upgrade-card">
    <!-- Top accent line -->
    <div class="upgrade-card__accent" aria-hidden="true"></div>
    
    <!-- Premium badge -->
    <div class="upgrade-card__badge">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
      </svg>
      <span>PRO</span>
    </div>

    <div class="upgrade-content">
      <div class="upgrade-icon">
        <CrownIcon />
      </div>
      <div class="upgrade-text">
        <h3 class="upgrade-title">{{ $t('upgrade.title') }}</h3>
        <p class="upgrade-desc">{{ $t('upgrade.description') }}</p>
      </div>

      <div class="features-list">
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>{{ $t('upgrade.features.unlimitedBacktests') }}</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>{{ $t('upgrade.features.botSlots') }}</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>{{ $t('upgrade.features.realtimeData') }}</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>{{ $t('upgrade.features.prioritySupport') }}</span>
        </div>
      </div>

      <div class="pricing">
        <span class="price">{{ $t('upgrade.price') }}</span>
        <span class="period">{{ $t('upgrade.period') }}</span>
        <span class="original-price">{{ $t('upgrade.originalPrice') }}</span>
      </div>

      <button class="upgrade-btn" type="button" data-test="upgrade-cta" @click="emit('upgrade')">
        <SparkleIcon />
        {{ $t('upgrade.cta') }}
      </button>

      <p class="trial-text">{{ $t('upgrade.trial') }}</p>
    </div>

    <!-- Subtle decorative elements -->
    <div class="decorative-glow glow-1" aria-hidden="true"></div>
    <div class="decorative-glow glow-2" aria-hidden="true"></div>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'

const emit = defineEmits<{
  (event: 'upgrade'): void
}>()

const CrownIcon = () => h('svg', {
  width: 32,
  height: 32,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 1.5,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('defs', {}, [
    h('linearGradient', {
      id: 'crown-gradient',
      x1: '0%',
      y1: '0%',
      x2: '100%',
      y2: '100%'
    }, [
      h('stop', { offset: '0%', 'stop-color': '#9A7B3A' }),
      h('stop', { offset: '100%', 'stop-color': '#B8944F' })
    ])
  ]),
  h('path', {
    d: 'm2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14',
    stroke: 'url(#crown-gradient)',
    fill: 'none'
  })
])

const CheckIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 1.75,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: '8', cy: '8', r: '7', fill: 'currentColor', opacity: '0.15' }),
  h('path', { points: '5 8l2 2 4-4' })
])

const SparkleIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'currentColor'
}, [
  h('path', {
    d: 'M8 1l-1.27 3.87a1.33 1.33 0 0 1-0.85 0.85L2 7l3.87 1.27a1.33 1.33 0 0 1 0.85 0.85L8 13l1.27-3.87a1.33 1.33 0 0 1 0.85-0.85L14 7l-3.87-1.27a1.33 1.33 0 0 1-0.85-0.85L8 1z',
    opacity: '0.9'
  })
])
</script>

<style scoped>
/* ── Premium Color Tokens ── */
.upgrade-card {
  --gold: #9A7B3A;
  --gold-light: #B8944F;
  --gold-dim: rgba(154, 123, 58, 0.1);
  --gold-glow: rgba(154, 123, 58, 0.18);
  --gold-text: #7A6230;
  --card-bg: linear-gradient(168deg, rgba(154, 123, 58, 0.04) 0%, var(--color-surface) 40%);
  --border-color: var(--gold-glow);
  --accent-glow: rgba(154, 123, 58, 0.12);
  
  position: relative;
  overflow: hidden;
  height: 100%;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm), 0 0 0 1px var(--gold-dim), 0 0 30px var(--accent-glow);
  transition: box-shadow 280ms ease, border-color 280ms ease, transform 280ms ease;
}

/* Dark theme overrides */
:root[data-theme="dark"] .upgrade-card {
  --gold: #C9A962;
  --gold-light: #E2CA8A;
  --gold-dim: rgba(201, 169, 98, 0.15);
  --gold-glow: rgba(201, 169, 98, 0.25);
  --gold-text: #C9A962;
  --card-bg: linear-gradient(168deg, rgba(201, 169, 98, 0.06) 0%, rgba(10, 15, 29, 0.85) 35%, rgba(10, 15, 29, 0.7) 100%);
  --border-color: var(--gold-glow);
  --accent-glow: rgba(201, 169, 98, 0.08);
}

.upgrade-card:hover {
  box-shadow: var(--shadow-md), 0 0 0 1px var(--gold-glow), 0 0 40px var(--accent-glow);
  transform: translateY(-2px);
}

/* ── Top Accent Line ── */
.upgrade-card__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), var(--gold-light), var(--gold), transparent);
  opacity: 0.7;
}

/* ── Premium Badge ── */
.upgrade-card__badge {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  box-shadow: 0 2px 8px var(--gold-dim);
  z-index: 2;
}

/* ── Content ── */
.upgrade-content {
  position: relative;
  z-index: 1;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.upgrade-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gold-dim) 0%, rgba(154, 123, 58, 0.05) 100%);
  border: 1px solid var(--gold-glow);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
  color: var(--gold-text);
}

.upgrade-text {
  margin-bottom: var(--spacing-md);
}

.upgrade-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs);
  letter-spacing: -0.01em;
}

.upgrade-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--line-height-relaxed);
}

/* ── Features List ── */
.features-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.check-icon {
  color: var(--gold-text);
  flex-shrink: 0;
}

/* ── Pricing ── */
.pricing {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.price {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
}

.period {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.original-price {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-decoration: line-through;
  margin-left: var(--spacing-sm);
}

/* ── Upgrade Button ── */
.upgrade-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: 11px 14px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 200ms ease;
  overflow: hidden;
  box-shadow: 0 2px 12px var(--gold-dim);
}

.upgrade-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 200ms ease;
}

.upgrade-btn:hover {
  background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 100%);
  box-shadow: 0 4px 16px var(--gold-glow);
  transform: translateY(-1px);
}

.upgrade-btn:hover::before {
  opacity: 1;
}

.upgrade-btn:active {
  transform: translateY(0);
}

/* ── Trial Text ── */
.trial-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-align: center;
  margin-top: var(--spacing-md);
}

/* ── Decorative Glows ── */
.decorative-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
}

.glow-1 {
  width: 150px;
  height: 150px;
  top: -50px;
  right: -50px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
  opacity: 0.6;
}

.glow-2 {
  width: 100px;
  height: 100px;
  bottom: -30px;
  left: -30px;
  background: radial-gradient(circle, rgba(154, 123, 58, 0.08) 0%, transparent 70%);
  opacity: 0.4;
}
</style>
