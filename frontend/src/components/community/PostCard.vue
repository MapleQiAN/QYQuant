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
        <img
          v-if="post.author.avatar_url"
          :src="post.author.avatar_url"
          :alt="post.author.nickname || '用户头像'"
          class="avatar"
          data-test="post-author-avatar-image"
        />
        <div v-else class="avatar avatar-fallback" data-test="post-author-avatar-fallback">
          {{ post.author.nickname?.slice(0, 1).toUpperCase() || 'Q' }}
        </div>
        <div class="author-info">
          <div class="nickname">{{ post.author.nickname || '匿名用户' }}</div>
          <div class="meta">{{ formatRelativeTime(post.created_at) }}</div>
        </div>
      </div>
      <RouterLink v-if="!detailMode" class="detail-link" :to="detailHref">
        查看详情
        <svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </RouterLink>
    </header>

    <p class="content">{{ post.content }}</p>

    <section v-if="post.strategy" class="strategy-card">
      <div class="strategy-header">
        <svg class="strategy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
        <div class="strategy-title">{{ post.strategy.name }}</div>
      </div>
      <div class="strategy-meta">
        <span class="strategy-tag">{{ post.strategy.category || '未分类' }}</span>
        <span class="strategy-metric positive">收益 {{ post.strategy.returns }}</span>
        <span class="strategy-metric negative">回撤 {{ post.strategy.max_drawdown }}</span>
      </div>
    </section>

    <footer class="actions">
      <button class="action" :class="{ active: post.liked }" @click.stop="toggleLike">
        <svg v-if="post.liked" class="action-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <svg v-else class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span>{{ post.likes_count }}</span>
      </button>

      <button class="action" :class="{ active: post.collected }" @click.stop="toggleCollect">
        <svg v-if="post.collected" class="action-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
        <svg v-else class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
        <span>收藏</span>
      </button>

      <RouterLink class="action link" :to="detailHref">
        <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span>{{ post.comments_count }}</span>
      </RouterLink>
    </footer>
  </article>
</template>

<style scoped>
.post-card {
  display: grid;
  gap: 18px;
  padding: 24px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.post-card::after {
  content: "";
  position: absolute;
  height: 4px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
  border-radius: 0 0 14px 14px;
}

.post-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
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
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--color-border);
}

.avatar-fallback {
  display: grid;
  place-items: center;
  background: var(--color-primary);
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  border: 2px solid var(--color-border);
}

.author-info {
  display: grid;
  gap: 2px;
}

.nickname {
  font-weight: 800;
  font-size: 15px;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.meta {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
  padding: 6px 12px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
  white-space: nowrap;
}

.detail-link:hover {
  color: var(--color-primary);
  background: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.detail-icon {
  width: 13px;
  height: 13px;
}

.content {
  margin: 0;
  line-height: 1.75;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  font-size: 15px;
}

.strategy-card {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border);
  position: relative;
  overflow: hidden;
}

.strategy-card::before {
  content: "";
  position: absolute;
  width: 8px;
  left: 0;
  top: 12px;
  bottom: 12px;
  background: var(--color-accent);
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  opacity: 0.9;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-icon {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.strategy-title {
  font-weight: 800;
  font-size: 14px;
  color: var(--color-text-primary);
}

.strategy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.strategy-tag {
  display: inline-flex;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 700;
}

.strategy-metric {
  display: inline-flex;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  border: 2px solid transparent;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.strategy-metric.positive {
  background: var(--color-down-bg);
  color: var(--color-down);
  border-color: rgba(46, 125, 50, 0.2);
}

.strategy-metric.negative {
  background: var(--color-up-bg);
  color: var(--color-up);
  border-color: rgba(212, 57, 59, 0.2);
}

.actions {
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  padding: 7px 14px;
  background: transparent;
  color: var(--color-text-secondary);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.action:hover {
  border-color: var(--color-border-hover);
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  transform: translateY(-1px);
}

.action.active {
  border-color: var(--color-danger);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.action-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .post-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
