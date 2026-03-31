<template>
  <div class="learn-shell">
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

          <div v-if="section.kind === 'map'" class="card-grid">
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
                  <dl class="parameter-facts">
                    <div class="parameter-fact">
                      <dt>{{ copy.definition }}</dt>
                      <dd>{{ parameter.definition }}</dd>
                    </div>
                    <div class="parameter-fact">
                      <dt>{{ copy.impact }}</dt>
                      <dd>{{ parameter.impact }}</dd>
                    </div>
                    <div class="parameter-fact">
                      <dt>{{ copy.pitfall }}</dt>
                      <dd>{{ parameter.pitfall }}</dd>
                    </div>
                    <div class="parameter-fact">
                      <dt>{{ copy.practice }}</dt>
                      <dd>{{ parameter.practice }}</dd>
                    </div>
                  </dl>
                </article>
              </div>
            </article>
          </div>

          <div v-else-if="section.kind === 'metrics'" class="split-layout">
            <div class="card-grid">
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
            <div class="card-grid">
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

          <div v-else-if="section.kind === 'roadmap'" class="card-grid">
            <article v-for="phase in section.roadmap" :key="phase.window" class="panel-card roadmap-card">
              <span class="panel-kicker">{{ phase.window }}</span>
              <h3 class="panel-title">{{ phase.focus }}</h3>
              <p class="panel-copy">{{ phase.output }}</p>
            </article>
          </div>

          <div v-else-if="section.kind === 'resources'" class="split-layout">
            <div class="card-grid">
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
  padding: 6px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-primary-border);
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-size: clamp(14px, 0.95vw, 15px);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
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
  font-family: 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
  font-weight: 600;
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
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', 'STSong', Georgia, serif;
  color: var(--color-text-secondary);
  line-height: 1.55;
  font-size: clamp(14px, 1vw, 16px);
}

.hero-summary-grid,
.card-grid {
  display: grid;
  gap: var(--spacing-md);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.summary-card,
.panel-card,
.parameter-group,
.side-panel {
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
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
  grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
  gap: var(--spacing-lg);
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
}

.section-header-block {
  display: grid;
  gap: 10px;
  margin-bottom: var(--spacing-md);
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
  margin-top: 14px;
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
  gap: 12px;
}

.parameter-group__header {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

.parameter-list {
  display: grid;
  gap: 10px;
}

.parameter-card {
  padding: 13px 15px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.parameter-name {
  margin-bottom: 10px;
}

.parameter-facts {
  display: grid;
  gap: 8px;
  margin: 0;
}

.parameter-fact {
  display: grid;
  gap: 3px;
}

.parameter-facts dt {
  color: var(--color-primary);
  font-size: clamp(12px, 0.88vw, 13px);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.split-layout {
  display: grid;
  gap: var(--spacing-md);
  grid-template-columns: minmax(0, 1.45fr) minmax(240px, 0.8fr);
  align-items: start;
}

.side-panel {
  position: sticky;
  top: calc(var(--nav-height) + var(--spacing-lg));
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

:global(:root[data-theme='light']) .learn-shell {
  gap: 20px;
}

:global(:root[data-theme='light']) .terminal-hero {
  background:
    linear-gradient(180deg, rgba(30, 90, 168, 0.05) 0%, rgba(255, 255, 255, 0.98) 72%);
  border-color: rgba(30, 90, 168, 0.14);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

:global(:root[data-theme='light']) .learn-section,
:global(:root[data-theme='light']) .learn-rail {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 252, 0.98) 100%);
  border-color: rgba(30, 90, 168, 0.12);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

:global(:root[data-theme='light']) .summary-card,
:global(:root[data-theme='light']) .panel-card,
:global(:root[data-theme='light']) .parameter-group,
:global(:root[data-theme='light']) .side-panel,
:global(:root[data-theme='light']) .workflow-item,
:global(:root[data-theme='light']) .parameter-card,
:global(:root[data-theme='light']) .syllabus-link {
  background: #ffffff;
  border-color: rgba(30, 90, 168, 0.1);
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
}

:global(:root[data-theme='light']) .hero-badge,
:global(:root[data-theme='light']) .section-eyebrow,
:global(:root[data-theme='light']) .panel-kicker,
:global(:root[data-theme='light']) .rail-label {
  background: rgba(30, 90, 168, 0.09);
  border-color: rgba(30, 90, 168, 0.18);
  color: var(--color-primary-dark);
}

:global(:root[data-theme='light']) .principle-chip,
:global(:root[data-theme='light']) .panel-tag {
  background: rgba(248, 250, 252, 0.96);
  border-color: rgba(30, 90, 168, 0.1);
  color: #4b5563;
}

:global(:root[data-theme='light']) .summary-value,
:global(:root[data-theme='light']) .summary-label,
:global(:root[data-theme='light']) .panel-title,
:global(:root[data-theme='light']) .parameter-name,
:global(:root[data-theme='light']) .hero-title,
:global(:root[data-theme='light']) .section-title,
:global(:root[data-theme='light']) .syllabus-link__label {
  color: #0f172a;
}

:global(:root[data-theme='light']) .hero-subtitle,
:global(:root[data-theme='light']) .section-description,
:global(:root[data-theme='light']) .panel-copy,
:global(:root[data-theme='light']) .rail-copy,
:global(:root[data-theme='light']) .summary-detail,
:global(:root[data-theme='light']) .workflow-checkpoint,
:global(:root[data-theme='light']) .metric-watch,
:global(:root[data-theme='light']) .checklist,
:global(:root[data-theme='light']) .mini-list,
:global(:root[data-theme='light']) .parameter-facts dd,
:global(:root[data-theme='light']) .syllabus-link__meta {
  color: #5b6778;
}

:global(:root[data-theme='light']) .workflow-index {
  background: rgba(30, 90, 168, 0.1);
  color: var(--color-primary-dark);
}

:global(:root[data-theme='light']) .parameter-facts dt,
:global(:root[data-theme='light']) .resource-link {
  color: var(--color-primary-dark);
}

:global(:root[data-theme='light']) .syllabus-link:hover,
:global(:root[data-theme='light']) .resource-card:hover {
  background: rgba(30, 90, 168, 0.06);
  border-color: rgba(30, 90, 168, 0.22);
}

@media (max-width: 1200px) {
  .learn-workspace,
  .split-layout {
    grid-template-columns: 1fr;
  }

  .learn-rail,
  .side-panel {
    position: static;
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
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
