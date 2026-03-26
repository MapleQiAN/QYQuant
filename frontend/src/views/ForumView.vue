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
        <div class="hero-badge">绀惧尯涓婚摼璺?/div>
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
      <p v-else-if="feedMode === 'all'" class="login-tip">鐧诲綍鍚庡嵆鍙彂甯栥€佺偣璧炪€佹敹钘忓拰璇勮銆?/p>

      <p v-if="communityStore.error && !communityStore.posts.length" class="status error">
        {{ communityStore.error }}
      </p>
      <p v-else-if="communityStore.loadingFeed && !communityStore.posts.length" class="status">
        甯栧瓙鍔犺浇涓€?
      </p>
      <div v-else-if="communityStore.posts.length" class="feed">
        <PostCard v-for="post in communityStore.posts" :key="post.id" :post="post" />
      </div>
      <p v-else class="status">杩樻病鏈夊笘瀛愶紝鍙戜竴鏉¤瘯璇曘€?/p>

      <button v-if="communityStore.posts.length && communityStore.hasMorePosts" class="load-more" @click="loadMore">
        鍔犺浇鏇村
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
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.18), transparent 32%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(15, 118, 110, 0.92));
  color: #fff;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: clamp(28px, 4vw, 40px);
}

.view-subtitle {
  margin: 0;
  max-width: 640px;
  color: rgba(255, 255, 255, 0.76);
}

.hero-badge {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
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
  background: rgba(255, 255, 255, 0.94);
  color: var(--color-text-muted);
  font: inherit;
  cursor: pointer;
}

.feed-switch__button.active {
  background: #0f172a;
  color: #fff;
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
  background: rgba(255, 255, 255, 0.94);
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
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
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
