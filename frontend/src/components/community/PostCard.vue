<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { CommunityPost } from '../../types/community'
import { useCommunityStore } from '../../stores/useCommunityStore'

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
  post: CommunityPost
  detailMode?: boolean
}>()

const communityStore = useCommunityStore()

const detailHref = computed(() => `/forum/posts/${props.post.id}`)

async function toggleLike() {
  await communityStore.toggleLike(props.post.id)
}

async function toggleCollect() {
  await communityStore.toggleCollect(props.post.id)
}
</script>

<template>
  <article class="post-card">
    <header class="post-header">
      <div class="author">
        <div class="avatar">{{ post.author.nickname?.slice(0, 1) || 'Q' }}</div>
        <div>
          <div class="nickname">{{ post.author.nickname || '匿名用户' }}</div>
          <div class="meta">{{ formatRelativeTime(post.created_at) }}</div>
        </div>
      </div>
      <RouterLink v-if="!detailMode" class="detail-link" :to="detailHref">查看详情</RouterLink>
    </header>

    <p class="content">{{ post.content }}</p>

    <section v-if="post.strategy" class="strategy-card">
      <div class="strategy-title">{{ post.strategy.name }}</div>
      <div class="strategy-meta">
        <span>{{ post.strategy.category || '未分类' }}</span>
        <span>收益 {{ post.strategy.returns }}</span>
        <span>回撤 {{ post.strategy.max_drawdown }}</span>
      </div>
    </section>

    <footer class="actions">
      <button class="action" :class="{ active: post.liked }" @click.stop="toggleLike">
        点赞 {{ post.likes_count }}
      </button>
      <button class="action" :class="{ active: post.collected }" @click.stop="toggleCollect">
        收藏
      </button>
      <RouterLink class="action link" :to="detailHref">
        评论 {{ post.comments_count }}
      </RouterLink>
    </footer>
  </article>
</template>

<style scoped>
.post-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.post-header,
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: var(--color-text-inverse);
  font-weight: 700;
}

.nickname {
  font-weight: 600;
  color: var(--color-text-primary);
}

.meta,
.detail-link {
  color: var(--color-text-muted);
  font-size: 14px;
}

.detail-link,
.link {
  text-decoration: none;
}

.content {
  margin: 0;
  line-height: 1.7;
  color: var(--color-text-primary);
  white-space: pre-wrap;
}

.strategy-card {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08), rgba(15, 118, 110, 0.08));
}

.strategy-title {
  font-weight: 600;
}

.strategy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.actions {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.action {
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 8px 14px;
  background: var(--color-surface);
  color: var(--color-text-primary);
  font: inherit;
  cursor: pointer;
}

.action.active {
  border-color: rgba(14, 165, 233, 0.32);
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
}

@media (max-width: 768px) {
  .post-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
