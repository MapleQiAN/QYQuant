<template>
  <aside v-if="enabled" :class="['chat-sidebar', { 'chat-sidebar--collapsed': collapsed }]">
    <div class="chat-sidebar__toggle" @click="collapsed = !collapsed">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    </div>

    <template v-if="!collapsed">
      <div class="chat-sidebar__header">
        <span class="chat-sidebar__eyebrow">AI</span>
        <h3 class="chat-sidebar__title">{{ $t('backtestReport.chatTitle') }}</h3>
        <p v-if="contextHint" class="chat-sidebar__context">
          {{ contextHint }}
          <button class="chat-sidebar__context-clear" @click="$emit('clear-context')">&times;</button>
        </p>
      </div>

      <div ref="messagesRef" class="chat-sidebar__messages">
        <article v-for="message in messages" :key="message.id" :class="['chat-message', `chat-message--${message.role}`]">
          <strong>{{ message.role === 'user' ? 'You' : 'AI' }}</strong>
          <p>{{ message.message }}</p>
        </article>
      </div>

      <form class="chat-sidebar__form" @submit.prevent="sendMessage">
        <input
          v-model="draft"
          class="chat-sidebar__input"
          data-test="chat-input"
          :disabled="loading"
          :placeholder="$t('backtestReport.chatPlaceholder')"
        />
        <button class="btn btn-primary" data-test="chat-send" type="submit" :disabled="!canSend">
          {{ loading ? '...' : $t('backtestReport.chatSend') }}
        </button>
      </form>
    </template>
  </aside>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { fetchReportChatHistory, sendReportChatMessage } from '../../../api/reports'
import type { BacktestAiChatMessage } from '../../../types/Backtest'

const props = defineProps<{
  reportId: string
  enabled: boolean
  contextHint?: string
}>()

defineEmits<{ 'clear-context': [] }>()

const draft = ref('')
const loading = ref(false)
const collapsed = ref(false)
const messages = ref<BacktestAiChatMessage[]>([])
const messagesRef = ref<HTMLElement | null>(null)

const canSend = computed(() => !loading.value && draft.value.trim().length > 0)

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function loadHistory() {
  if (!props.reportId) return
  try {
    const response = await fetchReportChatHistory(props.reportId)
    messages.value = response.messages
    scrollToBottom()
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
    messages.value = [
      ...messages.value,
      { id: `local-${Date.now()}`, role: 'user', message },
    ]
    scrollToBottom()
    const answer = await sendReportChatMessage(props.reportId, message)
    messages.value = [...messages.value, answer]
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

watch(() => props.reportId, () => { void loadHistory() })
onMounted(() => { void loadHistory() })
</script>

<style scoped>
.chat-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-left: 2px solid var(--color-border);
  background: var(--color-surface);
  overflow: hidden;
}

.chat-sidebar--collapsed {
  grid-template-rows: auto;
}

.chat-sidebar__toggle {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-xs);
  cursor: pointer;
  color: var(--color-text-muted);
}

.chat-sidebar__toggle:hover {
  color: var(--color-primary);
}

.chat-sidebar__header {
  display: grid;
  gap: 4px;
}

.chat-sidebar__eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chat-sidebar__title {
  margin: 0;
  font-size: var(--font-size-md);
}

.chat-sidebar__context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.chat-sidebar__context-clear {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: var(--font-size-md);
  line-height: 1;
  padding: 0 4px;
}

.chat-sidebar__messages {
  overflow-y: auto;
  display: grid;
  gap: var(--spacing-sm);
  align-content: start;
}

.chat-message {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.chat-message--assistant {
  border-color: color-mix(in srgb, var(--color-primary) 40%, var(--color-border));
}

.chat-message p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.chat-message strong {
  font-size: var(--font-size-xs);
}

.chat-sidebar__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-xs);
}

.chat-sidebar__input {
  min-width: 0;
  padding: 8px 10px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50vh;
    border-left: none;
    border-top: 2px solid var(--color-border);
    z-index: 100;
  }
}

@media print {
  .chat-sidebar {
    display: none;
  }
}
</style>
