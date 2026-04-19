<template>
  <section class="chat-panel" data-test="chat-panel">
    <div class="chat-panel__header">
      <span class="chat-panel__eyebrow">AI Chat</span>
      <h3 class="chat-panel__title">报告问答</h3>
      <p class="chat-panel__subtitle">
        {{ enabled ? '围绕本次回测报告提问。' : '当前套餐暂未开放报告问答。' }}
      </p>
    </div>

    <div class="chat-panel__messages">
      <article v-for="message in messages" :key="message.id" :class="['chat-message', `chat-message--${message.role}`]">
        <strong>{{ message.role }}</strong>
        <p>{{ message.message }}</p>
      </article>
    </div>

    <form class="chat-panel__form" @submit.prevent="sendMessage">
      <input
        v-model="draft"
        class="chat-panel__input"
        data-test="chat-input"
        :disabled="!enabled || loading"
        placeholder="例如：这次回测最大的风险是什么？"
      />
      <button class="btn btn-primary" data-test="chat-send" type="submit" :disabled="!canSend">
        {{ loading ? '发送中...' : '发送' }}
      </button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchReportChatHistory, sendReportChatMessage } from '../../../api/reports'
import type { BacktestAiChatMessage } from '../../../types/Backtest'

const props = defineProps<{
  reportId: string
  enabled: boolean
}>()

const draft = ref('')
const loading = ref(false)
const messages = ref<BacktestAiChatMessage[]>([])

const canSend = computed(() => props.enabled && !loading.value && draft.value.trim().length > 0)

async function loadHistory() {
  if (!props.reportId) return
  try {
    const response = await fetchReportChatHistory(props.reportId)
    messages.value = response.messages
  } catch {
    messages.value = []
  }
}

async function sendMessage() {
  if (!canSend.value) return
  const message = draft.value.trim()
  draft.value = ''
  loading.value = true
  try {
    messages.value.push({
      id: `local-${Date.now()}`,
      role: 'user',
      message,
    })
    const answer = await sendReportChatMessage(props.reportId, message)
    messages.value.push(answer)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadHistory()
})
</script>

<style scoped>
.chat-panel {
  display: grid;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.chat-panel__header {
  display: grid;
  gap: 6px;
}

.chat-panel__eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chat-panel__title,
.chat-panel__subtitle,
.chat-message p {
  margin: 0;
}

.chat-panel__subtitle,
.chat-message p {
  color: var(--color-text-secondary);
}

.chat-panel__messages {
  display: grid;
  gap: var(--spacing-sm);
}

.chat-message {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.chat-message--assistant {
  border-color: color-mix(in srgb, var(--color-primary) 40%, var(--color-border));
}

.chat-panel__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-sm);
}

.chat-panel__input {
  min-width: 0;
  padding: 10px 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

@media (max-width: 640px) {
  .chat-panel__form {
    grid-template-columns: 1fr;
  }
}
</style>
