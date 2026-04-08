<template>
  <div class="learn-shell" :class="{ 'learn-shell--zh': isZh }">
    <section class="terminal-hero card">
      <div class="hero-copy">
        <span class="hero-badge">{{ content.badge }}</span>
        <h1 class="hero-title editorial-title">{{ content.title }}</h1>
        <p class="hero-subtitle">{{ content.subtitle }}</p>
      </div>

      <div class="hero-summary-grid">
        <article v-for="stat in content.stats" :key="stat.label" class="summary-card">
          <span class="summary-value">{{ stat.value }}</span>
          <span class="summary-label">{{ stat.label }}</span>
          <p class="summary-detail">{{ stat.detail }}</p>
        </article>
      </div>

      <div class="hero-principles">
        <span v-for="principle in content.principles" :key="principle" class="principle-chip">
          {{ principle }}
        </span>
      </div>
    </section>

    <div class="learn-workspace">
      <aside class="learn-rail card">
        <div class="rail-header">
          <span class="rail-label">{{ copy.railLabel }}</span>
          <p class="rail-copy">{{ copy.railCopy }}</p>
        </div>

        <nav class="syllabus-list" :aria-label="copy.railLabel">
          <a
            v-for="item in content.syllabus"
            :key="item.id"
            class="syllabus-link"
            :href="`#${item.id}`"
          >
            <span class="syllabus-link__label">{{ item.label }}</span>
            <span class="syllabus-link__meta">{{ item.meta }}</span>
          </a>
        </nav>
      </aside>

      <div class="learn-panels">
        <section
          v-for="section in content.sections"
          :id="section.id"
          :key="section.id"
          class="learn-section card"
        >
          <div class="section-header-block">
            <span class="section-eyebrow">{{ section.eyebrow }}</span>
            <h2 class="section-title editorial-title">{{ section.title }}</h2>
            <p class="section-description">{{ section.description }}</p>
          </div>

          <div v-if="section.kind === 'map'" class="card-grid card-grid--map">
            <article v-for="card in section.cards" :key="card.title" class="panel-card">
              <h3 class="panel-title">{{ card.title }}</h3>
              <p class="panel-copy">{{ card.text }}</p>
              <div class="tag-row">
                <span v-for="tag in card.tags" :key="tag" class="panel-tag">{{ tag }}</span>
              </div>
            </article>
          </div>

          <ol v-else-if="section.kind === 'workflow'" class="workflow-list">
            <li v-for="(step, index) in section.steps" :key="step.title" class="workflow-item">
              <div class="workflow-index">{{ index + 1 }}</div>
              <div class="workflow-main">
                <h3 class="panel-title">{{ step.title }}</h3>
                <p class="panel-copy">{{ step.text }}</p>
                <p class="workflow-checkpoint">{{ copy.checkpoint }} {{ step.checkpoint }}</p>
              </div>
            </li>
          </ol>

          <div v-else-if="section.kind === 'parameters'" class="parameter-groups">
            <article v-for="group in section.groups" :key="group.title" class="parameter-group">
              <header class="parameter-group__header">
                <h3 class="panel-title">{{ group.title }}</h3>
                <p class="panel-copy">{{ group.description }}</p>
              </header>

              <div class="parameter-list">
                <article
                  v-for="parameter in group.parameters"
                  :key="parameter.name"
                  class="parameter-card"
                >
                  <h4 class="parameter-name">{{ parameter.name }}</h4>
                  <p class="parameter-definition">{{ parameter.definition }}</p>
                  <dl class="parameter-facts">
                    <div class="parameter-fact">
                      <dt>{{ copy.impact }}</dt>
                      <dd>{{ parameter.impact }}</dd>
                    </div>
                    <div class="parameter-fact">
                      <dt>{{ copy.pitfall }}</dt>
                      <dd>{{ parameter.pitfall }}</dd>
                    </div>
                    <div class="parameter-fact parameter-fact--wide">
                      <dt>{{ copy.practice }}</dt>
                      <dd>{{ parameter.practice }}</dd>
                    </div>
                  </dl>
                </article>
              </div>
            </article>
          </div>

          <div v-else-if="section.kind === 'metrics'" class="split-layout">
            <div class="card-grid card-grid--metrics">
              <article v-for="metric in section.metrics" :key="metric.title" class="panel-card">
                <span class="panel-kicker">{{ metric.formula }}</span>
                <h3 class="panel-title">{{ metric.title }}</h3>
                <p class="panel-copy">{{ metric.text }}</p>
                <p class="metric-watch">{{ copy.watch }} {{ metric.watch }}</p>
              </article>
            </div>

            <aside class="side-panel">
              <span class="panel-kicker">{{ copy.riskChecklist }}</span>
              <ul class="checklist">
                <li v-for="item in section.checklist" :key="item">{{ item }}</li>
              </ul>
            </aside>
          </div>

          <div v-else-if="section.kind === 'ai'" class="split-layout">
            <div class="card-grid card-grid--ai">
              <article v-for="module in section.modules" :key="module.title" class="panel-card">
                <h3 class="panel-title">{{ module.title }}</h3>
                <p class="panel-copy">{{ module.text }}</p>

                <div class="mini-block">
                  <span class="panel-kicker">{{ copy.useCases }}</span>
                  <ul class="mini-list">
                    <li v-for="item in module.useCases" :key="item">{{ item }}</li>
                  </ul>
                </div>

                <div class="mini-block">
                  <span class="panel-kicker">{{ copy.controls }}</span>
                  <ul class="mini-list">
                    <li v-for="item in module.controls" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </article>
            </div>

            <aside class="side-panel">
              <span class="panel-kicker">{{ copy.governance }}</span>
              <ul class="checklist">
                <li v-for="item in section.governance" :key="item">{{ item }}</li>
              </ul>
            </aside>
          </div>

          <div v-else-if="section.kind === 'roadmap'" class="card-grid card-grid--roadmap">
            <article v-for="phase in section.roadmap" :key="phase.window" class="panel-card roadmap-card">
              <span class="panel-kicker">{{ phase.window }}</span>
              <h3 class="panel-title">{{ phase.focus }}</h3>
              <p class="panel-copy">{{ phase.output }}</p>
            </article>
          </div>

          <div v-else-if="section.kind === 'resources'" class="split-layout">
            <div class="card-grid card-grid--resources">
              <a
                v-for="resource in section.resources"
                :key="resource.href"
                class="panel-card resource-card"
                :href="resource.href"
                target="_blank"
                rel="noreferrer"
              >
                <h3 class="panel-title">{{ resource.title }}</h3>
                <p class="panel-copy">{{ resource.text }}</p>
                <span class="resource-link">{{ copy.openReference }}</span>
              </a>
            </div>

            <aside class="side-panel">
              <span class="panel-kicker">{{ copy.commonPitfalls }}</span>
              <ul class="checklist">
                <li v-for="item in section.pitfalls" :key="item">{{ item }}</li>
              </ul>
            </aside>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { learnContentByLocale } from '../data/learn-content'

const { locale } = useI18n()
const isZh = computed(() => locale.value.startsWith('zh'))

const content = computed(() => {
  if (isZh.value) {
    return learnContentByLocale.zh
  }

  return learnContentByLocale.en.sections.length > 0 ? learnContentByLocale.en : learnContentByLocale.zh
})

const copy = computed(() =>
  isZh.value
    ? {
        railLabel: '学习索引',
        railCopy: '先用左侧目录锁定知识层级，再进入参数、风控和 AI 模块。',
        checkpoint: '检查点：',
        definition: '定义',
        impact: '影响',
        pitfall: '常见误区',
        practice: '实战建议',
        watch: '观察重点：',
        riskChecklist: '风险清单',
        useCases: '应用场景',
        controls: '控制要点',
        governance: '治理与合规',
        openReference: '打开参考站点',
        commonPitfalls: '常见误区',
      }
    : {
        railLabel: 'Syllabus',
        railCopy: 'Use the left rail to lock the knowledge layer before drilling into details.',
        checkpoint: 'Checkpoint:',
        definition: 'Definition',
        impact: 'Impact',
        pitfall: 'Common mistake',
        practice: 'Practical note',
        watch: 'Watch:',
        riskChecklist: 'Risk checklist',
        useCases: 'Use cases',
        controls: 'Controls',
        governance: 'Governance',
        openReference: 'Open reference',
        commonPitfalls: 'Common pitfalls',
      },
)
</script>

<style scoped>
.learn-shell {
  width: 100%;
  min-width: 0;
  display: grid;
  gap: var(--spacing-lg);
}

.terminal-hero,
.learn-section,
.learn-rail {
  border-color: var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.terminal-hero {
  padding: clamp(20px, 2.4vw, 32px);
  display: grid;
  gap: var(--spacing-lg);
}

.hero-copy {
  display: grid;
  gap: 12px;
  max-width: 78ch;
}

.hero-badge,
.section-eyebrow,
.panel-kicker,
.rail-label {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 5px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-primary-border);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: clamp(12px, 0.85vw, 13px);
  font-weight: var(--font-weight-semibold);
}

.hero-title,
.section-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: clamp(28px, 2.7vw, 44px);
  line-height: 1.06;
  letter-spacing: -0.03em;
}

.editorial-title {
  font-weight: 700;
}

.hero-subtitle,
.section-description,
.panel-copy,
.rail-copy,
.summary-detail,
.workflow-checkpoint,
.metric-watch,
.checklist,
.mini-list,
.parameter-facts dd {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.55;
  font-size: clamp(14px, 1vw, 16px);
}

.hero-summary-grid,
.card-grid {
  display: grid;
  gap: var(--spacing-md);
  align-items: stretch;
  grid-auto-rows: 1fr;
}

.hero-summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.card-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-card,
.panel-card,
.parameter-group,
.side-panel {
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 100%;
}

.summary-value {
  display: block;
  font-size: clamp(26px, 3vw, 36px);
  line-height: 1;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-bold);
}

.summary-label {
  display: block;
  margin-top: 10px;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.summary-detail {
  margin-top: 6px;
  font-size: clamp(14px, 0.95vw, 15px);
}

.hero-principles {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.principle-chip,
.panel-tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  font-size: clamp(13px, 0.9vw, 14px);
}

.learn-workspace {
  display: grid;
  grid-template-columns: minmax(232px, 264px) minmax(0, 1fr);
  gap: clamp(18px, 2vw, 28px);
  align-items: start;
}

.learn-rail {
  position: sticky;
  top: calc(var(--nav-height) + var(--spacing-lg));
  padding: var(--spacing-lg);
}

.rail-header {
  display: grid;
  gap: 10px;
}

.syllabus-list {
  display: grid;
  gap: 10px;
  margin-top: var(--spacing-md);
}

.syllabus-link {
  display: grid;
  gap: 3px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  text-decoration: none;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.syllabus-link:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.syllabus-link__label {
  font-weight: var(--font-weight-semibold);
  font-size: clamp(14px, 0.95vw, 15px);
}

.syllabus-link__meta {
  color: var(--color-text-muted);
  font-size: clamp(12px, 0.88vw, 13px);
}

.learn-panels {
  min-width: 0;
  display: grid;
  gap: var(--spacing-lg);
}

.learn-section {
  padding: clamp(20px, 2.2vw, 30px);
  display: grid;
  gap: clamp(18px, 1.8vw, 24px);
}

.section-header-block {
  display: grid;
  gap: 10px;
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.section-description {
  max-width: 76ch;
}

.panel-title,
.parameter-name {
  margin: 0;
  color: var(--color-text-primary);
  font-size: clamp(19px, 1.2vw, 24px);
  line-height: 1.2;
}

.panel-copy {
  margin-top: 8px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
  padding-top: 4px;
}

.workflow-list {
  display: grid;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.workflow-item {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 12px;
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.workflow-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: 21px;
  font-weight: var(--font-weight-bold);
}

.workflow-main {
  display: grid;
  gap: 6px;
}

.workflow-checkpoint,
.metric-watch {
  margin-top: 4px;
}

.parameter-groups {
  display: grid;
  gap: var(--spacing-lg);
}

.parameter-group__header {
  display: grid;
  gap: 8px;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.parameter-list {
  display: grid;
  gap: var(--spacing-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
}

.parameter-card {
  padding: clamp(16px, 1.6vw, 24px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  transition: border-color var(--transition-fast);
}

.parameter-card:hover {
  border-color: var(--color-border-hover);
}

.parameter-name {
  margin-bottom: 6px;
  font-size: clamp(17px, 1.15vw, 20px);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.01em;
}

.parameter-definition {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-secondary);
  font-size: clamp(14px, 1vw, 16px);
  line-height: 1.55;
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.parameter-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  margin: 0;
}

.parameter-fact {
  display: grid;
  gap: 4px;
  align-content: start;
}

.parameter-fact--wide {
  grid-column: 1 / -1;
}

.parameter-facts dt {
  color: var(--color-primary);
  font-size: clamp(11px, 0.82vw, 12px);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.split-layout {
  display: grid;
  gap: var(--spacing-lg);
  grid-template-columns: minmax(0, 1.6fr) minmax(260px, 0.9fr);
  align-items: start;
}

.side-panel {
  position: static;
}

.card-grid--map,
.card-grid--roadmap {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.card-grid--metrics,
.card-grid--ai,
.card-grid--resources {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.checklist,
.mini-list {
  margin: 14px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
}

.mini-block + .mini-block {
  margin-top: 14px;
}

.resource-card {
  text-decoration: none;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.resource-card:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
}

.resource-link {
  display: inline-flex;
  margin-top: 14px;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.roadmap-card {
  border-left: 3px solid var(--color-primary);
}

@media (max-width: 1360px) {
  .hero-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1440px) {
  .card-grid--map,
  .card-grid--roadmap {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .learn-workspace,
  .split-layout {
    grid-template-columns: 1fr;
  }

  .learn-rail {
    position: static;
  }

  .parameter-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .terminal-hero,
  .learn-rail,
  .learn-section {
    padding: var(--spacing-md);
  }

  .workflow-item {
    grid-template-columns: 1fr;
  }

  .hero-summary-grid,
  .card-grid,
  .parameter-list {
    grid-template-columns: 1fr;
  }

  .parameter-facts {
    grid-template-columns: 1fr;
  }

  .parameter-fact--wide {
    grid-column: auto;
  }
}

/* Chinese typography — scoped to zh locale */
.learn-shell--zh .hero-title,
.learn-shell--zh .section-title,
.learn-shell--zh .panel-title,
.learn-shell--zh .parameter-name,
.learn-shell--zh .summary-label,
.learn-shell--zh .hero-badge,
.learn-shell--zh .section-eyebrow,
.learn-shell--zh .principle-chip {
  font-family: var(--font-zh-display);
}

.learn-shell--zh .hero-subtitle,
.learn-shell--zh .section-description,
.learn-shell--zh .panel-copy,
.learn-shell--zh .rail-copy,
.learn-shell--zh .summary-detail,
.learn-shell--zh .parameter-definition,
.learn-shell--zh .parameter-facts dd,
.learn-shell--zh .workflow-checkpoint,
.learn-shell--zh .metric-watch,
.learn-shell--zh .checklist,
.learn-shell--zh .mini-list {
  font-family: var(--font-zh-body);
}

.learn-shell--zh .syllabus-link__label {
  font-family: var(--font-zh-display);
}

.learn-shell--zh .syllabus-link__meta,
.learn-shell--zh .rail-label {
  font-family: var(--font-zh-body);
}

.learn-shell--zh .summary-value {
  font-family: var(--font-zh-display);
}
</style>
