<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import CommentSection from '../components/community/CommentSection.vue'
import PostCard from '../components/community/PostCard.vue'
import { useCommunityStore } from '../stores/useCommunityStore'

const route = useRoute()
const communityStore = useCommunityStore()

const postId = computed(() => String(route.params.postId || ''))
const post = computed(() => communityStore.postDetailById[postId.value] || null)

watch(
  postId,
  (value) => {
    if (value) {
      void communityStore.fetchPostDetail(value)
    }
  },
  { immediate: true }
)
</script>

<template>
  <section class="view">
    <div class="container detail-layout">
      <p v-if="communityStore.loadingPostDetail && !post" class="status">帖子加载中…</p>
      <p v-else-if="communityStore.error && !post" class="status error">{{ communityStore.error }}</p>
      <template v-else-if="post">
        <PostCard :post="post" detail-mode />
        <CommentSection :post-id="postId" />
      </template>
      <p v-else class="status">帖子不存在或暂时不可见。</p>
    </div>
  </section>
</template>

<style scoped>
.view {
  width: 100%;
}

.detail-layout {
  display: grid;
  gap: 20px;
}

.status {
  margin: 0;
  padding: 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-text-muted);
}

.status.error {
  color: #c53030;
}
</style>
