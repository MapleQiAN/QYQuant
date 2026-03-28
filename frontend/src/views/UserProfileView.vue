<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import UserPostList from '../components/user/UserPostList.vue'
import UserProfileCard from '../components/user/UserProfileCard.vue'
import UserStrategyList from '../components/user/UserStrategyList.vue'
import { useUserProfileStore } from '../stores/useUserProfileStore'
import { useUserStore } from '../stores/user'

type TabKey = 'strategies' | 'posts'

const route = useRoute()
const userProfileStore = useUserProfileStore()
const userStore = useUserStore()

const activeTab = ref<TabKey>('strategies')
const notFound = ref(false)

const userId = computed(() => String(route.params.id || ''))
const profile = computed(() => userProfileStore.profileById[userId.value] || null)
const strategies = computed(() => userProfileStore.strategiesByUserId[userId.value] || null)
const posts = computed(() => userProfileStore.postsByUserId[userId.value] || null)
const isOwnProfile = computed(() => Boolean(userStore.profile.id) && userStore.profile.id === userId.value)

const hasMoreStrategies = computed(() => {
  const value = strategies.value
  if (!value) return false
  return value.page * value.per_page < value.total
})

const hasMorePosts = computed(() => {
  const value = posts.value
  if (!value) return false
  return value.page * value.per_page < value.total
})

watch(
  userId,
  async (value) => {
    if (!value) {
      return
    }

    notFound.value = false

    try {
      await userProfileStore.fetchProfile(value)
    } catch (error: any) {
      notFound.value = error?.status === 404
      return
    }

    await ensureTabLoaded(activeTab.value)
  },
  { immediate: true }
)

watch(activeTab, async (tab) => {
  await ensureTabLoaded(tab)
})

async function ensureTabLoaded(tab: TabKey) {
  if (!userId.value || notFound.value) {
    return
  }

  if (tab === 'strategies' && !strategies.value) {
    await userProfileStore.fetchUserStrategies(userId.value)
    return
  }

  if (tab === 'posts' && !posts.value) {
    await userProfileStore.fetchUserPosts(userId.value)
  }
}

function switchTab(tab: TabKey) {
  activeTab.value = tab
}

function loadMoreStrategies() {
  if (!strategies.value) {
    return
  }
  void userProfileStore.fetchUserStrategies(userId.value, strategies.value.page + 1, strategies.value.per_page)
}

function loadMorePosts() {
  if (!posts.value) {
    return
  }
  void userProfileStore.fetchUserPosts(userId.value, posts.value.page + 1, posts.value.per_page)
}
</script>

<template>
  <section class="view">
    <div class="container profile-layout">
      <div v-if="userProfileStore.loadingProfile && !profile" class="skeleton-shell">
        <div class="skeleton card"></div>
        <div class="skeleton body"></div>
      </div>

      <div v-else-if="notFound" class="feedback not-found">
        <h1>404</h1>
        <p>该用户不存在，或主页暂不可访问。</p>
      </div>

      <p v-else-if="userProfileStore.error && !profile" class="feedback error">
        {{ userProfileStore.error }}
      </p>

      <template v-else-if="profile">
        <UserProfileCard :profile="profile" :editable="isOwnProfile" />

        <section class="content-panel">
          <div class="tab-row">
            <button
              class="tab"
              :class="{ active: activeTab === 'strategies' }"
              data-test="tab-strategies"
              type="button"
              @click="switchTab('strategies')"
            >
              策略
            </button>
            <button
              class="tab"
              :class="{ active: activeTab === 'posts' }"
              data-test="tab-posts"
              type="button"
              @click="switchTab('posts')"
            >
              帖子
            </button>
          </div>

          <UserStrategyList
            v-if="activeTab === 'strategies'"
            :items="strategies?.items || []"
            :loading="userProfileStore.loadingStrategies"
            :has-more="hasMoreStrategies"
            @load-more="loadMoreStrategies"
          />

          <UserPostList
            v-else
            :items="posts?.items || []"
            :loading="userProfileStore.loadingPosts"
            :has-more="hasMorePosts"
            @load-more="loadMorePosts"
          />
        </section>
      </template>
    </div>
  </section>
</template>

<style scoped>
.view {
  width: 100%;
}

.profile-layout {
  display: grid;
  gap: 20px;
}

.skeleton-shell {
  display: grid;
  gap: 20px;
}

.skeleton {
  border-radius: 24px;
  background: linear-gradient(90deg, var(--color-border-light), var(--color-surface-hover), var(--color-border-light));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.skeleton.card {
  min-height: 160px;
}

.skeleton.body {
  min-height: 280px;
}

.feedback {
  padding: 28px;
  border-radius: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
}

.feedback.error {
  color: var(--color-danger);
}

.feedback.not-found h1,
.feedback.not-found p {
  margin: 0;
}

.feedback.not-found p {
  margin-top: 10px;
  color: var(--color-text-muted);
}

.content-panel {
  display: grid;
  gap: 16px;
}

.tab-row {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  justify-self: start;
}

.tab {
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  cursor: pointer;
}

.tab.active {
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}
</style>
