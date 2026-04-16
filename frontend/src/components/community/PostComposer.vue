<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useCommunityStore } from '../../stores/useCommunityStore'
import { useStrategiesStore } from '../../stores/strategies'
import { useUserStore } from '../../stores/user'

const communityStore = useCommunityStore()
const strategiesStore = useStrategiesStore()
const userStore = useUserStore()

const content = ref('')
const strategyId = ref('')

const characterCount = computed(() => content.value.length)
const charProgress = computed(() => Math.min((characterCount.value / 2000) * 100, 100))
const canSubmit = computed(() => {
  const trimmed = content.value.trim()
  return Boolean(userStore.profile.id) && trimmed.length > 0 && trimmed.length <= 2000 && !communityStore.submittingPost
})

const submitError = ref('')

async function submitPost() {
  if (!canSubmit.value) {
    return
  }
  submitError.value = ''

  try {
    await communityStore.createPost(content.value.trim(), strategyId.value || undefined)
    content.value = ''
    strategyId.value = ''
  } catch (error: unknown) {
    submitError.value = error instanceof Error ? error.message : '发布失败，请稍后重试'
  }
}

onMounted(() => {
  if (userStore.profile.id && strategiesStore.library.length === 0) {
    void strategiesStore.loadLibrary({ page: 1, perPage: 50 })
  }
})
</script>

<template>
  <section class="composer-card">
    <header class="composer-header">
      <div>
        <h2>发布帖子</h2>
        <p>分享你的策略心得、回测观察和交易复盘。</p>
      </div>
      <div class="char-counter" :class="{ danger: characterCount > 2000 }">
        <svg class="char-ring" viewBox="0 0 32 32">
          <circle class="char-ring__track" cx="16" cy="16" r="13" fill="none" stroke-width="3"/>
          <circle
            class="char-ring__fill"
            :class="{ danger: characterCount > 2000 }"
            cx="16" cy="16" r="13" fill="none" stroke-width="3"
            :stroke-dasharray="`${charProgress * 0.816} 81.6`"
            stroke-linecap="round"
          />
        </svg>
        <span>{{ characterCount }}/2000</span>
      </div>
    </header>

    <p v-if="submitError" class="error">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      {{ submitError }}
    </p>

    <textarea
      v-model="content"
      class="composer-input"
      placeholder="写点什么，告诉社区你最近在研究什么策略……"
      rows="5"
    />

    <div class="composer-footer">
      <label class="strategy-picker">
        <span class="picker-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
            <polyline points="17 6 23 6 23 12"/>
          </svg>
          关联策略
        </span>
        <select v-model="strategyId">
          <option value="">不关联</option>
          <option v-for="strategy in strategiesStore.library" :key="strategy.id" :value="strategy.id">
            {{ strategy.title || strategy.name }}
          </option>
        </select>
      </label>

      <button class="publish-button" :disabled="!canSubmit" @click="submitPost">
        <svg v-if="communityStore.submittingPost" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        {{ communityStore.submittingPost ? '发布中…' : '发布' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.composer-card {
  display: grid;
  gap: 16px;
  padding: 24px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.composer-card::before {
  content: "";
  position: absolute;
  width: 50px;
  height: 50px;
  background: var(--color-accent);
  border-radius: 50%;
  top: -16px;
  left: -16px;
  opacity: 0.9;
}

.composer-card::after {
  content: "";
  position: absolute;
  height: 5px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-accent);
  border-radius: 0 0 14px 14px;
}

.composer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.composer-header h2 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 900;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.composer-header p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.char-counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.char-counter span {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  color: var(--color-text-muted);
}

.char-counter.danger span {
  color: var(--color-danger);
}

.char-ring {
  width: 32px;
  height: 32px;
  transform: rotate(-90deg);
}

.char-ring__track {
  stroke: #e0e0dc;
  stroke-width: 3;
}

.char-ring__fill {
  stroke: var(--color-primary);
  transition: stroke-dasharray 0.2s ease;
  transform-origin: center;
}

.char-ring__fill.danger {
  stroke: var(--color-danger);
}

.error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  background: var(--color-danger-bg);
  border: 2px solid var(--color-danger);
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 600;
}

.error svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.composer-input {
  width: 100%;
  resize: vertical;
  min-height: 120px;
  padding: 14px 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  font: inherit;
  font-size: 14px;
  color: var(--color-text-primary);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.composer-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.composer-input::placeholder {
  color: var(--color-text-muted);
}

.composer-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.strategy-picker {
  display: grid;
  gap: 6px;
}

.picker-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.picker-label svg {
  width: 14px;
  height: 14px;
}

.strategy-picker select {
  min-width: 200px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.strategy-picker select:focus {
  border-color: var(--color-primary);
}

.publish-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  padding: 10px 20px;
  font: inherit;
  font-weight: 800;
  font-size: 14px;
  background: var(--color-accent);
  color: var(--color-text-primary);
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  white-space: nowrap;
}

.publish-button svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.publish-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.publish-button:active:not(:disabled) {
  transform: translateY(0);
}

.publish-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 0.8s linear infinite;
}

@media (max-width: 768px) {
  .composer-header,
  .composer-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .char-counter {
    flex-direction: row;
    align-self: flex-end;
  }

  .strategy-picker select {
    min-width: 0;
    width: 100%;
  }

  .publish-button {
    justify-content: center;
  }
}
</style>
