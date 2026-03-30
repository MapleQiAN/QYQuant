<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useCommunityStore } from '../../stores/useCommunityStore'
import { useUserStore } from '../../stores/user'

function formatRelativeTime(isoStr: string | null): string {
  if (!isoStr) return '刚刚'
  const date = new Date(isoStr)
  if (isNaN(date.getTime())) return '刚刚'
  const now = Date.now()
  const diffMs = now - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 30) return `${diffDay} 天前`
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const props = defineProps<{
  postId: string
}>()

const communityStore = useCommunityStore()
const userStore = useUserStore()
const content = ref('')

const comments = computed(() => communityStore.commentsByPostId[props.postId] || [])
const total = computed(() => communityStore.commentTotalsByPostId[props.postId] || 0)
const currentPage = computed(() => communityStore.commentPagesByPostId[props.postId] || 1)
const hasMore = computed(() => comments.value.length < total.value)
const submitError = ref('')
const canSubmit = computed(() => {
  const trimmed = content.value.trim()
  return Boolean(userStore.profile.id) && trimmed.length > 0 && trimmed.length <= 500 && !communityStore.submittingComment
})

async function loadComments(page = 1) {
  await communityStore.fetchComments(props.postId, page)
}

async function submitComment() {
  if (!canSubmit.value) {
    return
  }
  submitError.value = ''

  try {
    await communityStore.createComment(props.postId, content.value.trim())
    content.value = ''
  } catch (error: unknown) {
    submitError.value = error instanceof Error ? error.message : '评论发送失败，请稍后重试'
  }
}

watch(
  () => props.postId,
  (postId) => {
    if (postId) {
      void loadComments(1)
    }
  },
  { immediate: true }
)
</script>

<template>
  <section class="comment-section">
    <header class="comment-header">
      <div class="comment-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <h2>评论</h2>
      </div>
      <span v-if="total > 0" class="comment-badge">{{ total }}</span>
    </header>

    <div v-if="userStore.profile.id" class="comment-form">
      <textarea
        v-model="content"
        rows="4"
        maxlength="500"
        placeholder="补充你的看法、问题或回测观察……"
      />
      <div class="comment-form-footer">
        <span class="char-count" :class="{ danger: content.length > 480 }">{{ content.length }}/500</span>
        <button :disabled="!canSubmit" @click="submitComment">
          <svg v-if="communityStore.submittingComment" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          {{ communityStore.submittingComment ? '发送中…' : '发送评论' }}
        </button>
      </div>
      <p v-if="submitError" class="submit-error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ submitError }}
      </p>
    </div>

    <p v-else class="comment-tip">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
      登录后可以参与评论。
    </p>

    <div v-if="comments.length" class="comment-list">
      <article v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-avatar">{{ comment.author.nickname?.slice(0, 1).toUpperCase() || 'Q' }}</div>
        <div class="comment-body">
          <header class="comment-item-header">
            <strong class="comment-author">{{ comment.author.nickname || '匿名用户' }}</strong>
            <span class="comment-time">{{ formatRelativeTime(comment.created_at) }}</span>
          </header>
          <p>{{ comment.content }}</p>
        </div>
      </article>
    </div>
    <p v-else class="empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      还没有评论，来做第一个发言的人。
    </p>

    <button v-if="hasMore" class="load-more" @click="loadComments(currentPage + 1)">
      加载更多评论
    </button>
  </section>
</template>

<style scoped>
.comment-section {
  display: grid;
  gap: 20px;
  padding: 24px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-surface);
}

.comment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.comment-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-title svg {
  width: 18px;
  height: 18px;
  color: var(--color-text-muted);
}

.comment-title h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.comment-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--color-primary-bg);
  color: var(--color-primary-light);
  font-size: 12px;
  font-weight: 600;
}

.comment-form {
  display: grid;
  gap: 10px;
}

.comment-form textarea {
  width: 100%;
  resize: vertical;
  min-height: 100px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  font: inherit;
  font-size: 14px;
  color: var(--color-text-primary);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.comment-form textarea:focus {
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.comment-form textarea::placeholder {
  color: var(--color-text-muted);
}

.comment-form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.char-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.char-count.danger {
  color: var(--color-danger);
}

.comment-form button,
.load-more {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 0;
  border-radius: 999px;
  padding: 9px 18px;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.comment-form button svg,
.load-more svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.comment-form button:hover:not(:disabled),
.load-more:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);
}

.comment-form button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.load-more {
  justify-self: center;
}

.submit-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: 13px;
}

.submit-error svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.comment-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-size: 14px;
}

.comment-tip svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.comment-list {
  display: grid;
  gap: 2px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--color-border-light);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 2px;
}

.comment-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 6px;
}

.comment-item-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.comment-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.comment-body p {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
}

.empty {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 20px;
  border-radius: 12px;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-size: 14px;
  justify-content: center;
}

.empty svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 0.8s linear infinite;
}
</style>
