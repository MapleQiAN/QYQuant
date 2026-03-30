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
        <div class="hero-content">
          <div class="hero-eyebrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            社区广场
          </div>
          <h1 class="view-title">{{ $t('pages.forumTitle') }}</h1>
          <p class="view-subtitle">{{ $t('pages.forumSubtitle') }}</p>
        </div>
        <div class="hero-decoration" aria-hidden="true">
          <div class="deco-ring deco-ring--1"/>
          <div class="deco-ring deco-ring--2"/>
          <div class="deco-ring deco-ring--3"/>
        </div>
      </header>

      <div class="feed-switch">
        <button
          class="feed-switch__button"
          :class="{ active: feedMode === 'all' }"
          type="button"
          @click="switchFeed('all')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          全部帖子
        </button>
        <button
          v-if="canViewCollections"
          class="feed-switch__button"
          :class="{ active: feedMode === 'collections' }"
          type="button"
          @click="switchFeed('collections')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
          我的收藏
        </button>
      </div>

      <PostComposer v-if="showComposer" />
      <div v-else-if="feedMode === 'all'" class="login-tip">
        <div class="login-tip__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
        </div>
        <div>
          <div class="login-tip__title">加入讨论</div>
          <p class="login-tip__text">登录后即可发帖、点赞、收藏和评论。</p>
        </div>
      </div>

      <div v-if="communityStore.error && !communityStore.posts.length" class="status error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ communityStore.error }}
      </div>
      <div v-else-if="communityStore.loadingFeed && !communityStore.posts.length" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <div class="skeleton-header">
            <div class="skeleton-avatar"/>
            <div class="skeleton-lines">
              <div class="skeleton-line skeleton-line--short"/>
              <div class="skeleton-line skeleton-line--xshort"/>
            </div>
          </div>
          <div class="skeleton-line skeleton-line--full"/>
          <div class="skeleton-line skeleton-line--full"/>
          <div class="skeleton-line skeleton-line--medium"/>
        </div>
      </div>
      <div v-else-if="communityStore.posts.length" class="feed">
        <PostCard v-for="post in communityStore.posts" :key="post.id" :post="post" />
      </div>
      <div v-else class="empty-state">
        <div class="empty-state__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="empty-state__title">还没有帖子</div>
        <p class="empty-state__text">发一条帖子，开启讨论。</p>
      </div>

      <button v-if="communityStore.posts.length && communityStore.hasMorePosts" class="load-more" @click="loadMore">
        <svg v-if="communityStore.loadingFeed" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
        {{ communityStore.loadingFeed ? '加载中…' : '加载更多' }}
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

/* ── Hero ── */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 32px 36px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, var(--color-primary-light), transparent 40%),
    linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  color: var(--color-text-inverse);
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 14px;
  backdrop-filter: blur(4px);
}

.hero-eyebrow svg {
  width: 14px;
  height: 14px;
}

.view-title {
  margin: 0 0 10px;
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
}

.view-subtitle {
  margin: 0;
  max-width: 520px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.75);
}

/* Decorative rings */
.hero-decoration {
  position: absolute;
  right: -40px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.deco-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  transform: translate(-50%, -50%);
}

.deco-ring--1 { width: 120px; height: 120px; }
.deco-ring--2 { width: 200px; height: 200px; }
.deco-ring--3 { width: 300px; height: 300px; }

/* ── Feed Switch ── */
.feed-switch {
  display: flex;
  gap: 8px;
  padding: 4px;
  border-radius: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  width: fit-content;
}

.feed-switch__button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 0;
  border-radius: 10px;
  padding: 9px 16px;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.feed-switch__button svg {
  width: 15px;
  height: 15px;
}

.feed-switch__button:hover {
  color: var(--color-text-secondary);
  background: var(--color-surface-hover);
}

.feed-switch__button.active {
  background: var(--color-primary);
  color: #fff;
}

/* ── Login Tip ── */
.login-tip {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.login-tip__icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--color-primary-bg);
  color: var(--color-primary-light);
  flex-shrink: 0;
}

.login-tip__icon svg {
  width: 20px;
  height: 20px;
}

.login-tip__title {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
  margin-bottom: 3px;
}

.login-tip__text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

/* ── Status / Error ── */
.status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 20px;
  border-radius: 16px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 14px;
}

.status.error {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.status svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* ── Skeleton Loading ── */
.skeleton-list {
  display: grid;
  gap: 16px;
}

.skeleton-card {
  display: grid;
  gap: 14px;
  padding: 24px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-surface);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-surface-elevated);
  flex-shrink: 0;
}

.skeleton-lines {
  flex: 1;
  display: grid;
  gap: 8px;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-line--xshort { width: 30%; }
.skeleton-line--short  { width: 50%; }
.skeleton-line--medium { width: 70%; }
.skeleton-line--full   { width: 100%; }

@keyframes shimmer {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ── Feed ── */
.feed {
  display: grid;
  gap: 16px;
}

/* ── Empty State ── */
.empty-state {
  display: grid;
  place-items: center;
  gap: 12px;
  padding: 48px 24px;
  border-radius: 20px;
  background: var(--color-surface);
  border: 1px dashed var(--color-border-strong);
  text-align: center;
}

.empty-state__icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
}

.empty-state__icon svg {
  width: 28px;
  height: 28px;
}

.empty-state__title {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text-secondary);
}

.empty-state__text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

/* ── Load More ── */
.load-more {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  justify-self: center;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 10px 22px;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.load-more svg {
  width: 16px;
  height: 16px;
}

.load-more:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-bg);
  color: var(--color-primary-light);
  transform: translateY(-1px);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 0.8s linear infinite;
}

@media (max-width: 768px) {
  .hero {
    padding: 24px;
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-decoration {
    display: none;
  }
}
</style>
