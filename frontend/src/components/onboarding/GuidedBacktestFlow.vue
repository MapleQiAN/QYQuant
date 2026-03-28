<template>
  <section v-if="visible" class="guided-card">
    <header class="guided-header">
      <div>
        <p class="guided-eyebrow">首次回测引导</p>
        <h2 class="guided-title">{{ stepConfig.title }}</h2>
      </div>
      <button class="guided-exit" type="button" data-test="guided-exit" @click="$emit('exit')">
        退出引导
      </button>
    </header>

    <div class="guided-steps">
      <span
        v-for="index in 4"
        :key="index"
        :class="['guided-pill', { active: step >= index }]"
      >
        {{ index }}/4
      </span>
    </div>

    <p class="guided-copy">{{ stepConfig.description }}</p>

    <article v-if="selectedStrategy" class="guided-strategy">
      <strong>{{ selectedStrategy.name }}</strong>
      <span>{{ selectedStrategy.symbol }}</span>
    </article>
    <p v-else-if="loading" class="guided-state">正在加载引导策略...</p>
    <p v-else-if="error" class="guided-state error">{{ error }}</p>

    <button
      v-if="stepConfig.action"
      class="guided-action"
      type="button"
      @click="stepConfig.action()"
    >
      {{ stepConfig.actionLabel }}
    </button>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchMarketplaceStrategies } from '../../api/strategies'
import type { Strategy } from '../../types/Strategy'

const emit = defineEmits<{
  (event: 'exit'): void
  (event: 'open-marketplace', strategyId: string): void
  (event: 'open-parameters', strategyId: string): void
  (event: 'open-report', jobId: string): void
  (event: 'complete'): void
}>()

const props = withDefaults(defineProps<{
  visible?: boolean
  step?: number
  jobId?: string
}>(), {
  visible: true,
  step: 1,
  jobId: '',
})

const loading = ref(false)
const error = ref('')
const strategies = ref<Strategy[]>([])

const selectedStrategy = computed(() => strategies.value[0] ?? null)

const stepConfig = computed(() => {
  if (props.step === 1) {
    return {
      title: '先到策略广场选一条新手策略',
      description: '我们已经帮你挑出 onboarding 专用策略，先从这条策略开始，避免第一次就在大量选项里迷路。',
      actionLabel: '前往策略广场',
      action: () => {
        if (selectedStrategy.value) {
          emit('open-marketplace', selectedStrategy.value.id)
        }
      },
    }
  }
  if (props.step === 2) {
    return {
      title: '确认参数并运行',
      description: '默认参数已经预填好，直接点运行即可。你不需要先理解所有参数，再开始第一次回测。',
      actionLabel: '前往参数页',
      action: () => {
        if (selectedStrategy.value) {
          emit('open-parameters', selectedStrategy.value.id)
        }
      },
    }
  }
  if (props.step === 3) {
    return {
      title: '等待系统生成报告',
      description: '回测正在运行中，系统会生成收益曲线和核心指标。第一次等待时，只需要盯住进度，不必反复切换页面。',
      actionLabel: props.jobId ? '查看回测报告' : '',
      action: props.jobId ? () => emit('open-report', props.jobId) : undefined,
    }
  }
  return {
    title: '查看首次回测结果',
    description: '现在重点看累计收益率、最大回撤和夏普比率，先建立“结果长什么样”的直觉。',
    actionLabel: '完成首次引导',
    action: () => emit('complete'),
  }
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    strategies.value = await fetchMarketplaceStrategies({ tag: 'onboarding' })
  } catch (err: any) {
    error.value = err?.message || '加载引导策略失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.guided-card {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 950;
  width: min(380px, calc(100vw - 32px));
  padding: 20px;
  border-radius: 18px;
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border);
  backdrop-filter: blur(16px);
}

.guided-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.guided-eyebrow {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.guided-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 20px;
}

.guided-exit {
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
}

.guided-steps {
  display: flex;
  gap: 8px;
  margin: 16px 0;
}

.guided-pill {
  border-radius: 999px;
  padding: 4px 10px;
  background: var(--color-background);
  color: #64748b;
  font-size: 12px;
}

.guided-pill.active {
  background: #f5e642;
  color: #1e293b;
}

.guided-copy {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.guided-strategy {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--color-background);
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.guided-state {
  margin-top: 14px;
  color: var(--color-text-muted);
}

.guided-state.error {
  color: var(--color-danger);
}

.guided-action {
  margin-top: 18px;
  width: 100%;
  border: none;
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  background: #1a1a1a;
  color: var(--color-text-inverse);
  cursor: pointer;
}
</style>
