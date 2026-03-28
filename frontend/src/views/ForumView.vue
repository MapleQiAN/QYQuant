<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PostCard from '../components/community/PostCard.vue'
import PostComposer from '../components/community/PostComposer.vue'
import { useCommunityStore } from '../stores/useCommunityStore'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const communityStore = useCommunityStore()
const userStore = useUserStore()

const feedMode = computed<'all' | 'collections'>(() =>
  route.query.view === 'collections' ? 'collections' : 'all'
)
const showComposer = computed(() => Boolean(userStore.profile.id) && feedMode.value === 'all')
const canViewCollections = computed(() => Boolean(userStore.profile.id))

watch(
  feedMode,
  () => {
    void loadFeed(1)
  },
  { immediate: true }
)

function loadMore() {
  if (communityStore.hasMorePosts) {
    void loadFeed(communityStore.currentPage + 1)
  }
}

async function loadFeed(page = 1) {
  if (feedMode.value === 'collections') {
    if (!userStore.profile.id) {
      await router.replace({ name: 'forum' })
      return
    }
    await communityStore.fetchCollections(page)
    return
  }

  await communityStore.fetchPosts(page)
}

function switchFeed(mode: 'all' | 'collections') {
  void router.push({
    name: 'forum',
    query: mode === 'collections' ? { view: 'collections' } : {}
  })
}
</script>

<template>
  <section class="view">
    <div class="container community-layout">
      <header class="hero">
        <div>
          <h1 class="view-title">{{ $t('pages.forumTitle') }}</h1>
          <p class="view-subtitle">{{ $t('pages.forumSubtitle') }}</p>
        </div>
        <div class="hero-badge">广场</div>
      </header>

      <div class="feed-switch">
        <button
          class="feed-switch__button"
          :class="{ active: feedMode === 'all' }"
          type="button"
          @click="switchFeed('all')"
        >
          全部帖子
        </button>
        <button
          v-if="canViewCollections"
          class="feed-switch__button"
          :class="{ active: feedMode === 'collections' }"
          type="button"
          @click="switchFeed('collections')"
        >
          我的收藏
        </button>
      </div>

      <PostComposer v-if="showComposer" />
      <p v-else-if="feedMode === 'all'" class="login-tip">登录后即可发帖、点赞、收藏和评论。</p>

      <p v-if="communityStore.error && !communityStore.posts.length" class="status error">
        {{ communityStore.error }}
      </p>
      <p v-else-if="communityStore.loadingFeed && !communityStore.posts.length" class="status">
        帖子加载中...
      </p>
      <div v-else-if="communityStore.posts.length" class="feed">
        <PostCard v-for="post in communityStore.posts" :key="post.id" :post="post" />
      </div>
      <p v-else class="status">还没有帖子,发一条试试。</p>

      <button v-if="communityStore.posts.length && communityStore.hasMorePosts" class="load-more" @click="loadMore">
        加载更多
      </button>
    </div>
  </section>
</template>

<style scoped>
.view {
  width: 100%;
}

.community-layout {
  display: grid;
  gap: 20px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, var(--color-primary-light), transparent 32%),
    linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  color: var(--color-text-inverse);
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: clamp(28px, 4vw, 40px);
}

.view-subtitle {
  margin: 0;
  max-width: 640px;
  color: var(--color-text-inverse);
}

.hero-badge {
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--color-surface-hover);
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.feed-switch {
  display: flex;
  gap: 12px;
}

.feed-switch__button {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  font: inherit;
  cursor: pointer;
}

.feed-switch__button.active {
  background: var(--color-primary-dark);
  color: var(--color-text-inverse);
}

.feed {
  display: grid;
  gap: 16px;
}

.status,
.login-tip {
  margin: 0;
  padding: 20px;
  border-radius: 18px;
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.status.error {
  color: #c53030;
}

.load-more {
  justify-self: center;
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font: inherit;
  cursor: pointer;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
