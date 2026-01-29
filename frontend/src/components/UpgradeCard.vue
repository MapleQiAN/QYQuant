<template>
  <div class="upgrade-card card-neumorphism">
    <div class="upgrade-content">
      <div class="upgrade-icon">
        <CrownIcon />
      </div>
      <div class="upgrade-text">
        <h3 class="upgrade-title">升级到 Pro</h3>
        <p class="upgrade-desc">解锁无限回测、更多机器人槽位和专业数据源</p>
      </div>
      
      <div class="features-list">
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>无限回测次数</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>10 个机器人槽位</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>实时市场数据</span>
        </div>
        <div class="feature-item">
          <CheckIcon class="check-icon" />
          <span>优先技术支持</span>
        </div>
      </div>
      
      <div class="pricing">
        <span class="price">¥99</span>
        <span class="period">/月</span>
        <span class="original-price">¥199</span>
      </div>
      
      <button class="upgrade-btn">
        <SparkleIcon />
        立即升级
      </button>
      
      <p class="trial-text">7 天免费试用，随时取消</p>
    </div>
    
    <!-- Decorative Elements -->
    <div class="decorative-circle circle-1"></div>
    <div class="decorative-circle circle-2"></div>
  </div>
</template>

<script setup lang="ts">
const CrownIcon = {
  template: `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"/></svg>`
}

const CheckIcon = {
  template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
}

const SparkleIcon = {
  template: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>`
}
</script>

<style scoped>
.upgrade-card {
  position: relative;
  overflow: hidden;
  height: 100%;
  background: linear-gradient(135deg, #fefefe 0%, #f8fafc 100%);
}

.upgrade-content {
  position: relative;
  z-index: 1;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.upgrade-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: white;
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-md);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.upgrade-text {
  margin-bottom: var(--spacing-md);
}

.upgrade-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs);
}

.upgrade-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--line-height-relaxed);
}

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
  color: var(--color-success);
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
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
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

.upgrade-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-md);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.upgrade-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.trial-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-align: center;
  margin-top: var(--spacing-md);
}

/* Decorative Elements */
.decorative-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.circle-1 {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, var(--color-primary-bg), transparent);
  top: -40px;
  right: -40px;
}

.circle-2 {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), transparent);
  bottom: 20px;
  left: -20px;
}
</style>
