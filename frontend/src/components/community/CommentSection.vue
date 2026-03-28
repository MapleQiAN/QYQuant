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
      <h2>评论</h2>
      <span>{{ total }} 条</span>
    </header>

    <div v-if="userStore.profile.id" class="comment-form">
      <textarea
        v-model="content"
        rows="4"
        maxlength="500"
        placeholder="补充你的看法、问题或回测观察……"
      />
      <div class="comment-form-footer">
        <span>{{ content.length }}/500</span>
        <button :disabled="!canSubmit" @click="submitComment">
          {{ communityStore.submittingComment ? '发送中…' : '发送评论' }}
        </button>
      </div>
      <p v-if="submitError" class="submit-error">{{ submitError }}</p>
    </div>

    <p v-else class="comment-tip">登录后可以参与评论。</p>

    <div v-if="comments.length" class="comment-list">
      <article v-for="comment in comments" :key="comment.id" class="comment-item">
        <header>
          <strong>{{ comment.author.nickname || '匿名用户' }}</strong>
          <span>{{ formatRelativeTime(comment.created_at) }}</span>
        </header>
        <p>{{ comment.content }}</p>
      </article>
    </div>
    <p v-else class="empty">还没有评论，来做第一个发言的人。</p>

    <button v-if="hasMore" class="load-more" @click="loadComments(currentPage + 1)">
      加载更多评论
    </button>
  </section>
</template>

<style scoped>
.comment-section {
  display: grid;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-surface);
}

.comment-header,
.comment-form-footer,
.comment-item header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.comment-header h2 {
  margin: 0;
}

.comment-form {
  display: grid;
  gap: 12px;
}

.comment-form textarea {
  width: 100%;
  resize: vertical;
  min-height: 100px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font: inherit;
}

.comment-form-footer span,
.comment-tip,
.empty,
.comment-item header span {
  color: var(--color-text-muted);
  font-size: 14px;
}

.comment-form button,
.load-more {
  justify-self: end;
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: var(--color-text-inverse);
  font: inherit;
  cursor: pointer;
}

.comment-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-error {
  margin: 0;
  color: #c53030;
  font-size: 14px;
}

.comment-list {
  display: grid;
  gap: 12px;
}

.comment-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--color-background);
}

.comment-item p {
  margin: 10px 0 0;
  white-space: pre-wrap;
}
</style>
