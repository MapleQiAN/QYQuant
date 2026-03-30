<template>
  <div class="learn-view">
    <section class="hero card card-accent">
      <div class="hero-copy">
        <span class="hero-badge">{{ content.badge }}</span>
        <h1 class="hero-title">{{ content.title }}</h1>
        <p class="hero-subtitle">{{ content.subtitle }}</p>
      </div>
      <div class="hero-stats">
        <div v-for="stat in content.stats" :key="stat.label" class="stat-chip">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </section>

    <section class="quick-nav card">
      <div class="quick-nav-header">
        <span class="section-title">{{ isZh ? '本页导航' : 'On this page' }}</span>
      </div>
      <div class="quick-nav-links">
        <a
          v-for="section in content.sections"
          :key="section.id"
          class="quick-link"
          :href="`#${section.id}`"
        >
          {{ section.title }}
        </a>
      </div>
    </section>

    <section
      v-for="section in content.sections"
      :id="section.id"
      :key="section.id"
      class="learn-section card"
    >
      <div class="learn-section-header">
        <span class="section-eyebrow">{{ section.eyebrow }}</span>
        <h2 class="learn-section-title">{{ section.title }}</h2>
        <p class="learn-section-description">{{ section.description }}</p>
      </div>

      <div v-if="'items' in section" class="topic-grid">
        <article v-for="item in section.items" :key="item.title" class="topic-card">
          <h3 class="topic-title">{{ item.title }}</h3>
          <p class="topic-text">{{ item.text }}</p>
        </article>
      </div>

      <ol v-else-if="'steps' in section" class="workflow-list">
        <li v-for="(step, index) in section.steps" :key="step.title" class="workflow-item">
          <div class="workflow-index">{{ index + 1 }}</div>
          <div class="workflow-body">
            <h3 class="topic-title">{{ step.title }}</h3>
            <p class="topic-text">{{ step.text }}</p>
          </div>
        </li>
      </ol>

      <div v-else-if="'metrics' in section" class="metrics-layout">
        <div class="topic-grid">
          <article v-for="metric in section.metrics" :key="metric.title" class="topic-card">
            <h3 class="topic-title">{{ metric.title }}</h3>
            <p class="topic-text">{{ metric.text }}</p>
          </article>
        </div>
        <aside class="warning-panel">
          <h3 class="warning-title">{{ isZh ? '新手风控提醒' : 'Risk reminders' }}</h3>
          <ul class="warning-list">
            <li v-for="warning in section.warnings" :key="warning">{{ warning }}</li>
          </ul>
        </aside>
      </div>

      <div v-else-if="'roadmap' in section" class="roadmap-grid">
        <article v-for="phase in section.roadmap" :key="phase.week" class="roadmap-card">
          <span class="roadmap-week">{{ phase.week }}</span>
          <h3 class="topic-title">{{ phase.focus }}</h3>
          <p class="topic-text">{{ phase.deliverable }}</p>
        </article>
      </div>

      <div v-else-if="'resources' in section" class="resources-layout">
        <div class="topic-grid">
          <a
            v-for="resource in section.resources"
            :key="resource.href"
            class="resource-card"
            :href="resource.href"
            target="_blank"
            rel="noreferrer"
          >
            <h3 class="topic-title">{{ resource.title }}</h3>
            <p class="topic-text">{{ resource.text }}</p>
            <span class="resource-link">{{ isZh ? '打开参考站点' : 'Open reference' }}</span>
          </a>
        </div>
        <aside class="warning-panel">
          <h3 class="warning-title">{{ isZh ? '常见误区' : 'Common pitfalls' }}</h3>
          <ul class="warning-list">
            <li v-for="pitfall in section.pitfalls" :key="pitfall">{{ pitfall }}</li>
          </ul>
        </aside>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { learnContentByLocale } from '../data/learn-content'

const { locale } = useI18n()
const isZh = computed(() => locale.value.startsWith('zh'))
const content = computed(() => (isZh.value ? learnContentByLocale.zh : learnContentByLocale.en))
</script>

<style scoped>
.learn-view {
  width: 100%;
  max-width: min(1280px, calc(100% - var(--spacing-lg) * 2));
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.hero {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl);
  overflow: hidden;
  background:
    radial-gradient(circle at top right, var(--color-primary-bg), transparent 35%),
    linear-gradient(135deg, var(--color-surface) 0%, var(--color-surface-elevated) 100%);
}

.hero-badge,
.section-eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: var(--radius-full);
  background: var(--color-primary-bg);
  border: 1px solid var(--color-primary-border);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.hero-title {
  margin: 0;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.08;
  letter-spacing: var(--letter-spacing-tight);
  color: var(--color-text-primary);
}

.hero-subtitle,
.learn-section-description,
.topic-text {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.hero-subtitle {
  max-width: 760px;
  font-size: var(--font-size-md);
}

.hero-stats {
  display: grid;
  gap: var(--spacing-sm);
  align-content: center;
}

.stat-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.02);
}

.stat-value {
  font-size: var(--font-size-xxxl);
  line-height: 1;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.quick-nav,
.learn-section {
  padding: var(--spacing-lg);
}

.quick-nav-header {
  margin-bottom: var(--spacing-sm);
}

.quick-nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.quick-link,
.resource-card {
  text-decoration: none;
}

.quick-link {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-surface-elevated);
  transition: all var(--transition-fast);
}

.quick-link:hover,
.resource-card:hover {
  border-color: var(--color-primary-border);
  color: var(--color-text-primary);
}

.learn-section-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.learn-section-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  color: var(--color-text-primary);
}

.topic-grid,
.roadmap-grid {
  display: grid;
  gap: var(--spacing-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.topic-card,
.roadmap-card,
.resource-card,
.warning-panel {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: linear-gradient(180deg, var(--color-surface-elevated) 0%, var(--color-surface) 100%);
}

.topic-title,
.warning-title {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
}

.workflow-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--spacing-sm);
}

.workflow-item {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: var(--spacing-md);
  align-items: flex-start;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.workflow-index {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #fff;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
}

.workflow-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metrics-layout,
.resources-layout {
  display: grid;
  grid-template-columns: 1.6fr 0.9fr;
  gap: var(--spacing-md);
}

.warning-panel {
  align-self: start;
}

.warning-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
  color: var(--color-text-secondary);
}

.roadmap-card {
  position: relative;
  overflow: hidden;
}

.roadmap-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-accent) 100%);
}

.roadmap-week,
.resource-link {
  display: inline-flex;
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
}

.resource-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  transition: all var(--transition-fast);
}

.resource-link {
  margin-top: auto;
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 1200px) {
  .learn-view {
    max-width: 100%;
  }

  .hero,
  .metrics-layout,
  .resources-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero,
  .quick-nav,
  .learn-section {
    padding: var(--spacing-md);
  }

  .topic-grid,
  .roadmap-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 28px;
  }
}
</style>
