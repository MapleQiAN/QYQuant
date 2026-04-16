<template>
  <div class="upgrade-card">
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
        {{ $t('upgrade.cta') }}
      </button>

      <p class="trial-text">{{ $t('upgrade.trial') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'

const emit = defineEmits<{
  (event: 'upgrade'): void
}>()

const CrownIcon = () => h('svg', {
  width: 28,
  height: 28,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 1.5,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'm2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14' })
])

const CheckIcon = () => h('svg', {
  width: 14,
  height: 14,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2.5,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M5 12l5 5L20 7' })
])
</script>

<style scoped>
.upgrade-card {
  height: 100%;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  transition: border-color var(--transition-normal);
}

.upgrade-card:hover {
  border-color: var(--color-border-hover);
}

.upgrade-card::after {
  content: "";
  position: absolute;
  width: 80px;
  height: 80px;
  background: var(--color-accent);
  bottom: -30px;
  right: -20px;
  transform: rotate(25deg);
  border-radius: 16px;
  opacity: 0.10;
}

.upgrade-content {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 1;
}

.upgrade-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-bg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
  color: var(--color-accent);
}

.upgrade-text {
  margin-bottom: var(--spacing-md);
}

.upgrade-title {
  font-size: var(--font-size-lg);
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs);
  letter-spacing: -0.01em;
}

.upgrade-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: 2px dashed var(--color-border-light);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

.pricing {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.price {
  font-size: var(--font-size-xxl);
  font-weight: 900;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  font-family: 'DM Mono', monospace;
}

.period {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 600;
}

.original-price {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-decoration: line-through;
  margin-left: var(--spacing-sm);
  font-weight: 600;
}

.upgrade-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 14px;
  font-size: var(--font-size-sm);
  font-weight: 800;
  background: var(--color-accent);
  color: var(--color-text-primary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: inherit;
}

.upgrade-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.upgrade-btn:active {
  opacity: 0.85;
}

.trial-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-align: center;
  margin-top: var(--spacing-sm);
  font-weight: 600;
}
</style>
