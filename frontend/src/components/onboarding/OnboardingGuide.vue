<template>
  <div v-if="visible" class="guide-shell">
    <div class="guide-overlay" />
    <section class="guide-card">
      <div class="guide-header">
        <div>
          <p class="guide-eyebrow">新手引导</p>
          <h2 class="guide-title">3 步快速上手 QYQuant</h2>
        </div>
        <button
          class="guide-skip"
          type="button"
          data-test="skip-onboarding"
          @click="$emit('skip')"
        >
          跳过引导
        </button>
      </div>

      <div class="guide-steps">
        <button
          v-for="step in steps"
          :key="step.id"
          :class="['guide-step', { active: step.id === currentStep }]"
          type="button"
          @click="currentStep = step.id"
        >
          <span class="guide-step-index">0{{ step.id }}</span>
          <span>{{ step.title }}</span>
        </button>
      </div>

      <article class="guide-body">
        <h3 class="guide-body-title">{{ activeStep.title }}</h3>
        <p class="guide-body-copy">{{ activeStep.description }}</p>
        <button class="guide-action" type="button" data-test="step-action" @click="handleAction">
          {{ activeStep.actionLabel }}
        </button>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const emit = defineEmits<{
  (event: 'skip'): void
  (event: 'focus-target', target: string): void
  (event: 'launch-guided-backtest'): void
  (event: 'complete'): void
}>()

const props = withDefaults(defineProps<{
  visible: boolean
  initialStep?: number
}>(), {
  initialStep: 1,
})

const steps = [
  {
    id: 1,
    title: '认识策略广场',
    description: '先找到平台里最适合新手的现成策略，知道从哪里开始看、从哪里开始选。',
    actionLabel: '高亮策略入口',
  },
  {
    id: 2,
    title: '一键回测策略',
    description: '跟着引导走一次完整回测，减少第一次配置参数时的犹豫成本。',
    actionLabel: '开始引导回测',
  },
  {
    id: 3,
    title: '查看回测报告',
    description: '完成首次回测后，直接在结果页看核心指标和收益曲线，形成第一轮认知。',
    actionLabel: '完成引导',
  },
]

const currentStep = ref(props.initialStep)
const activeStep = computed(() => steps.find((step) => step.id === currentStep.value) ?? steps[0])

watch(() => props.initialStep, (next) => {
  currentStep.value = next
})

function handleAction() {
  if (currentStep.value === 1) {
    emit('focus-target', 'strategy-library-entry')
    currentStep.value = 2
    return
  }
  if (currentStep.value === 2) {
    emit('launch-guided-backtest')
    return
  }
  emit('complete')
}
</script>

<style scoped>
.guide-shell {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.guide-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
}

.guide-card {
  position: relative;
  width: min(560px, 100%);
  border-radius: 16px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
}

.guide-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.guide-eyebrow {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.guide-title {
  margin: 0;
  color: var(--color-text-primary);
}

.guide-skip {
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
}

.guide-steps {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.guide-step {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
  cursor: pointer;
}

.guide-step.active {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.08);
}

.guide-step-index {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.guide-body-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 20px;
}

.guide-body-copy {
  margin: 10px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.guide-action {
  margin-top: 20px;
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  background: #1a1a1a;
  color: #fff;
  cursor: pointer;
}
</style>
