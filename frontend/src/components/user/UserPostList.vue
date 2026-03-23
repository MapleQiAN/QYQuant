<script setup lang="ts">
import type { UserPostItem } from '../../types/User'

defineProps<{
  items: UserPostItem[]
  loading?: boolean
  hasMore?: boolean
}>()

defineEmits<{
  (event: 'load-more'): void
}>()
</script>

<template>
  <section class="list-shell">
    <p v-if="loading && !items.length" class="status">帖子加载中...</p>
    <p v-else-if="!items.length" class="status">该用户暂未发布帖子。</p>
    <div v-else class="list">
      <article v-for="item in items" :key="item.id" class="post-card">
        <p class="content">{{ item.content }}</p>
        <footer class="meta">
          <span>点赞 {{ item.likes_count }}</span>
          <span>评论 {{ item.comments_count }}</span>
          <span>{{ item.created_at || '时间未知' }}</span>
        </footer>
      </article>
    </div>

    <button v-if="hasMore" class="load-more" type="button" @click="$emit('load-more')">加载更多帖子</button>
  </section>
</template>

<style scoped>
.list-shell,
.list {
  display: grid;
  gap: 16px;
}

.post-card,
.status {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.05);
}

.content {
  margin: 0;
  color: var(--color-text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 16px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.load-more {
  justify-self: center;
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font: inherit;
  cursor: pointer;
}
</style>
