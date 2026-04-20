<template>
  <template v-if="enabled">
    <button
      :class="['chat-fab', { 'chat-fab--open': open }]"
      data-test="chat-fab"
      title="AI Chat"
      @click="emit('update:open', !open)"
    >
      <svg v-if="!open" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>

    <aside :class="['chat-sidebar', { 'chat-sidebar--open': open }]">
      <div class="chat-sidebar__inner">
        <div class="chat-sidebar__accent" />

        <div class="chat-sidebar__header">
          <div class="chat-sidebar__brand">
            <div class="chat-sidebar__avatar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <span class="chat-sidebar__eyebrow">AI</span>
              <h3 class="chat-sidebar__title">{{ $t('backtestReport.chatTitle') }}</h3>
            </div>
          </div>
          <p v-if="contextHint" class="chat-sidebar__context">
            {{ contextHint }}
            <button class="chat-sidebar__context-clear" @click="emit('clear-context')">&times;</button>
          </p>
        </div>

        <div ref="messagesRef" class="chat-sidebar__messages">
          <div v-if="messages.length === 0 && !loading" class="chat-sidebar__empty">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <p>{{ $t('backtestReport.chatPlaceholder') }}</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            :class="['chat-bubble', `chat-bubble--${message.role}`]"
          >
            <span class="chat-bubble__sender">{{ message.role === 'user' ? 'You' : 'AI' }}</span>
            <p class="chat-bubble__text">{{ message.message }}</p>
          </article>

          <div v-if="loading" class="chat-typing">
            <span></span><span></span><span></span>
          </div>
        </div>

        <form class="chat-sidebar__form" @submit.prevent="sendMessage">
          <div class="chat-input-wrap">
            <input
              v-model="draft"
              class="chat-input"
              data-test="chat-input"
              :disabled="loading"
              :placeholder="$t('backtestReport.chatPlaceholder')"
            />
            <button class="chat-send" data-test="chat-send" type="submit" :disabled="!canSend">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </aside>
  </template>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { fetchReportChatHistory, sendReportChatMessage } from '../../../api/reports'
import type { BacktestAiChatMessage } from '../../../types/Backtest'

const props = defineProps<{
  reportId: string
  enabled: boolean
  contextHint?: string
  open: boolean
}>()

const emit = defineEmits<{
  'clear-context': []
  'update:open': [value: boolean]
}>()

const draft = ref('')
const loading = ref(false)
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

function handleEscape(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) {
    emit('update:open', false)
  }
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
onMounted(() => {
  void loadHistory()
  window.addEventListener('keydown', handleEscape)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
/* ─── Floating Toggle Dot ─── */
.chat-fab {
  position: fixed;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-primary);
  cursor: pointer;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-fab::before {
  content: "";
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 2px solid var(--color-primary);
  opacity: 0;
  animation: fab-ring 3s ease-out 2s infinite;
  pointer-events: none;
}

.chat-fab:hover {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
  transform: translateY(-50%) scale(1.08);
}

.chat-fab:hover::before {
  animation: none;
  opacity: 0;
}

.chat-fab--open {
  color: var(--color-text-muted);
  border-color: var(--color-border-light);
  box-shadow: var(--shadow-xs);
}

.chat-fab--open::before {
  display: none;
}

.chat-fab--open:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  border-color: var(--color-border);
  transform: translateY(-50%) scale(1.06);
  box-shadow: var(--shadow-sm);
}

@keyframes fab-ring {
  0% { opacity: 0; transform: scale(0.9); }
  40% { opacity: 0.5; }
  100% { opacity: 0; transform: scale(1.6); }
}

/* ─── Sidebar Panel ─── */
.chat-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 380px;
  z-index: 200;
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  will-change: transform;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.chat-sidebar--open {
  transform: translateX(0);
  pointer-events: auto;
}

.chat-sidebar__inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-left: 2px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

/* Accent gradient bar */
.chat-sidebar__accent {
  height: 3px;
  flex-shrink: 0;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent), var(--color-primary));
  background-size: 200% 100%;
}

/* ─── Header ─── */
.chat-sidebar__header {
  padding: 20px 20px 16px;
  border-bottom: 2px solid var(--color-border);
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--color-surface-elevated) 0%, var(--color-surface) 100%);
}

.chat-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-sidebar__avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--color-primary-bg);
  border: 2px solid var(--color-primary-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}

.chat-sidebar__eyebrow {
  display: block;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.chat-sidebar__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.chat-sidebar__context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 0;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  border: 1px dashed var(--color-border-light);
  font-size: 11px;
  color: var(--color-text-secondary);
}

.chat-sidebar__context-clear {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  margin-left: auto;
}

.chat-sidebar__context-clear:hover {
  color: var(--color-text-primary);
}

/* ─── Messages ─── */
.chat-sidebar__messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-sidebar__messages::-webkit-scrollbar {
  width: 4px;
}

.chat-sidebar__messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-sidebar__messages::-webkit-scrollbar-thumb {
  background: var(--color-border-light);
  border-radius: 2px;
}

.chat-sidebar__messages::-webkit-scrollbar-thumb:hover {
  background: var(--color-scrollbar-thumb-hover);
}

/* Empty state */
.chat-sidebar__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--color-text-muted);
  opacity: 0.45;
}

.chat-sidebar__empty p {
  margin: 0;
  font-size: 12px;
  text-align: center;
  line-height: 1.6;
}

/* ─── Chat Bubbles ─── */
.chat-bubble {
  max-width: 88%;
  padding: 10px 14px;
  border-radius: 12px;
}

.chat-bubble--user {
  align-self: flex-end;
  background: var(--color-surface-elevated);
  border: 1.5px solid var(--color-border-light);
  border-bottom-right-radius: 4px;
}

.chat-bubble--assistant {
  align-self: flex-start;
  background: var(--color-primary-bg);
  border: 1.5px solid var(--color-primary-border);
  border-bottom-left-radius: 4px;
}

.chat-bubble__sender {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
  color: var(--color-text-muted);
}

.chat-bubble--assistant .chat-bubble__sender {
  color: var(--color-primary);
}

.chat-bubble__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-primary);
}

/* ─── Typing Indicator ─── */
.chat-typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  align-self: flex-start;
  background: var(--color-primary-bg);
  border: 1.5px solid var(--color-primary-border);
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.chat-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  opacity: 0.4;
  animation: typing-dot 1.4s ease-in-out infinite;
}

.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-dot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ─── Input Form ─── */
.chat-sidebar__form {
  padding: 12px 16px 16px;
  border-top: 2px solid var(--color-border);
  flex-shrink: 0;
}

.chat-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 4px 4px 14px;
  border: 2px solid var(--color-border);
  border-radius: 24px;
  background: var(--color-surface);
  transition: border-color 0.15s ease;
}

.chat-input-wrap:focus-within {
  border-color: var(--color-primary);
}

.chat-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--color-text-primary);
  padding: 6px 0;
  font-family: inherit;
}

.chat-input::placeholder {
  color: var(--color-text-muted);
}

.chat-send {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s ease, transform 0.15s ease, opacity 0.2s ease;
}

.chat-send:disabled {
  opacity: 0.3;
  cursor: default;
}

.chat-send:not(:disabled):hover {
  background: var(--color-primary-dark);
  transform: scale(1.1);
}

.chat-send:not(:disabled):active {
  transform: scale(0.92);
}

/* ─── Responsive ─── */
@media (max-width: 768px) {
  .chat-sidebar {
    width: 100%;
    border-left: none;
    top: auto;
    height: 55vh;
    border-top: 2px solid var(--color-border);
    border-radius: 16px 16px 0 0;
    transform: translateY(100%);
  }

  .chat-sidebar--open {
    transform: translateY(0);
  }

  .chat-sidebar__inner {
    border-left: none;
    border-radius: 16px 16px 0 0;
    box-shadow: var(--shadow-lg);
  }

  .chat-fab {
    right: 16px;
    bottom: 24px;
    top: auto;
    transform: none;
  }

  .chat-fab:hover {
    transform: scale(1.1);
  }

  .chat-fab--open:hover {
    transform: scale(1.06);
  }

  .chat-fab::before {
    animation: none;
  }
}

@media print {
  .chat-sidebar,
  .chat-fab {
    display: none;
  }
}
</style>
