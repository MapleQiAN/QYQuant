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
      <span class="count" :class="{ danger: characterCount > 2000 }">{{ characterCount }}/2000</span>
    </header>

    <p v-if="submitError" class="error">{{ submitError }}</p>

    <textarea
      v-model="content"
      class="composer-input"
      placeholder="写点什么，告诉社区你最近在研究什么策略……"
      rows="5"
    />

    <div class="composer-footer">
      <label class="strategy-picker">
        <span>关联策略</span>
        <select v-model="strategyId">
          <option value="">不关联</option>
          <option v-for="strategy in strategiesStore.library" :key="strategy.id" :value="strategy.id">
            {{ strategy.title || strategy.name }}
          </option>
        </select>
      </label>

      <button class="publish-button" :disabled="!canSubmit" @click="submitPost">
        {{ communityStore.submittingPost ? '发布中…' : '发布' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.composer-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 252, 0.96));
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.composer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.composer-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.composer-header p {
  margin: 0;
  color: var(--color-text-muted);
}

.count {
  font-size: 13px;
  color: var(--color-text-muted);
}

.count.danger {
  color: #c53030;
}

.error {
  margin: 0;
  color: #c53030;
  font-size: 14px;
}

.composer-input {
  width: 100%;
  resize: vertical;
  min-height: 120px;
  padding: 16px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 16px;
  background: #fff;
  font: inherit;
  color: var(--color-text-primary);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.strategy-picker {
  display: grid;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.strategy-picker select {
  min-width: 220px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: #fff;
  color: var(--color-text-primary);
}

.publish-button {
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  font: inherit;
  font-weight: 600;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  cursor: pointer;
}

.publish-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .composer-header,
  .composer-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .strategy-picker select {
    min-width: 0;
    width: 100%;
  }
}
</style>
