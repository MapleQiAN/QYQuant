<template>
  <div class="dashboard-view">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-text">
          <h1 class="page-title">{{ $t('dashboard.title', { name: user.name }) }}</h1>
          <p class="page-subtitle">{{ $t('dashboard.subtitle') }}</p>
        </div>
        <div class="header-actions">
          <RouterLink class="btn btn-secondary" to="/settings">
            <SettingsIcon />
            {{ $t('common.settings') }}
          </RouterLink>
          <RouterLink class="btn btn-primary" to="/strategies">
            <PlusIcon />
            {{ $t('common.newStrategy') }}
          </RouterLink>
        </div>
      </div>
      <OnboardingGuide
        :visible="showOnboardingGuide"
        @skip="handleSkipOnboarding"
        @focus-target="userStore.setOnboardingHighlightTarget"
        @launch-guided-backtest="userStore.startGuidedBacktest()"
        @complete="handleSkipOnboarding"
      />

      <div class="dashboard-grid">
        <div class="grid-area-backtest">
          <BacktestCard
            :data="backtestsStore.latest"
            :loading="backtestsStore.loading"
            :error="backtestsStore.error"
            :symbol="backtestQuery.symbol"
            :timeframe="backtestQuery.interval"
            :data-source="backtestQuery.dataSource"
            @retry="loadBacktest"
            @refresh="loadBacktest"
            @timeframe-change="handleTimeframeChange"
            @data-source-change="handleDataSourceChange"
          />
        </div>

        <div class="grid-area-recent">
          <RecentList
            :title="$t('dashboard.recentTitle')"
            :strategies="strategiesStore.recent"
            :strategies-loading="strategiesStore.loading"
            :strategies-error="strategiesStore.error"
            :bots="botsStore.recent"
            :bots-loading="botsStore.loading"
            :bots-error="botsStore.error"
            @retry-strategies="strategiesStore.loadRecent"
            @retry-bots="botsStore.loadRecent"
            @open-strategy="handleOpenStrategy"
            @deploy-strategy="handleDeployStrategy"
            @open-bot="handleOpenBot"
            @toggle-bot="handleToggleBot"
            @view-all="handleViewAllRecent"
          />
        </div>

        <div class="grid-area-forum">
          <ForumMiniCard
            :posts="forumStore.posts"
            :loading="forumStore.loading"
            :error="forumStore.error"
            @retry="forumStore.loadHot"
            @view-all="handleOpenForum"
            @publish="handleOpenForumComposer"
            @bookmarks="handleOpenForumBookmarks"
            @open-post="handleOpenForumPost"
          />
        </div>

        <div class="grid-area-upgrade">
          <UpgradeCard @upgrade="handleOpenPricing" />
        </div>

        <div class="grid-area-progress">
          <ProgressCard />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import BacktestCard from '../components/BacktestCard.vue'
import ForumMiniCard from '../components/ForumMiniCard.vue'
import OnboardingGuide from '../components/onboarding/OnboardingGuide.vue'
import ProgressCard from '../components/ProgressCard.vue'
import RecentList from '../components/RecentList.vue'
import UpgradeCard from '../components/UpgradeCard.vue'
import { useBacktestsStore, useBotsStore, useForumStore, useStrategiesStore, useUserStore } from '../stores'
import { useSimulationStore } from '../stores/useSimulationStore'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.profile)
const showOnboardingGuide = computed(() =>
  Boolean(user.value.id) && !user.value.onboarding_completed && !userStore.guidedBacktestActive
)

const backtestsStore = useBacktestsStore()
const botsStore = useBotsStore()
const strategiesStore = useStrategiesStore()
const forumStore = useForumStore()
const simulationStore = useSimulationStore()
const backtestQuery = reactive({
  symbol: 'XAUUSD',
  interval: '1d',
  dataSource: 'auto'
})

const loadBacktest = () => {
  backtestsStore.loadLatest({ ...backtestQuery })
}

const handleTimeframeChange = (interval: string) => {
  backtestQuery.interval = interval
  loadBacktest()
}

const handleDataSourceChange = (dataSource: string) => {
  backtestQuery.dataSource = dataSource
  if (dataSource === 'freegold') {
    backtestQuery.interval = '1d'
  }
  loadBacktest()
}

onMounted(() => {
  void userStore.loadProfile?.()
  loadBacktest()
  botsStore.loadRecent()
  strategiesStore.loadRecent()
  forumStore.loadHot()
})

async function handleSkipOnboarding() {
  await userStore.markOnboardingCompleted(true)
  userStore.setOnboardingHighlightTarget(null)
}

async function handleOpenStrategy(strategyId: string) {
  await router.push({ name: 'strategy-parameters', params: { strategyId } })
}

async function handleDeployStrategy(strategyId: string) {
  await router.push({ name: 'bots', query: { create: '1', strategyId } })
}

async function handleOpenBot(botId: string) {
  await router.push({ name: 'bots', query: { botId, modal: 'detail' } })
}

async function handleToggleBot(botId: string, action: 'pause' | 'resume') {
  try {
    if (action === 'pause') {
      await simulationStore.pauseBot(botId)
    } else {
      await simulationStore.resumeBot(botId)
    }
    await botsStore.loadRecent()
  } catch {
    // Keep the dashboard preview stable if the preview action fails.
  }
}

async function handleViewAllRecent(tab: 'strategies' | 'bots') {
  await router.push(tab === 'bots' ? { name: 'bots' } : { name: 'strategy-library' })
}

async function handleOpenForum() {
  await router.push({ name: 'forum' })
}

async function handleOpenForumComposer() {
  await router.push({ name: 'forum', query: { compose: '1' } })
}

async function handleOpenForumBookmarks() {
  await router.push({ name: 'forum', query: { view: 'collections' } })
}

async function handleOpenForumPost(postId: string) {
  await router.push({ name: 'forum-post-detail', params: { postId } })
}

async function handleOpenPricing() {
  await router.push({ name: 'pricing' })
}

const SettingsIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 3 }),
  h('path', { d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z' })
])

const PlusIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M5 12h14' }),
  h('path', { d: 'M12 5v14' })
])
</script>

<style scoped>
.dashboard-view {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* Dashboard Grid - 12 Column System */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: auto auto;
  gap: var(--grid-gap);
  grid-template-areas:
    "backtest backtest backtest backtest backtest backtest backtest backtest recent recent recent recent"
    "forum forum forum forum upgrade upgrade upgrade upgrade progress progress progress progress";
}

.grid-area-backtest {
  grid-area: backtest;
}

.grid-area-recent {
  grid-area: recent;
}

.grid-area-forum {
  grid-area: forum;
}

.grid-area-upgrade {
  grid-area: upgrade;
}

.grid-area-progress {
  grid-area: progress;
}

/* Make cards fill their grid areas */
.grid-area-backtest > *,
.grid-area-recent > *,
.grid-area-forum > *,
.grid-area-upgrade > *,
.grid-area-progress > * {
  height: 100%;
}

/* Responsive Design */
@media (max-width: 1280px) {
  .dashboard-grid {
    grid-template-areas:
      "backtest backtest backtest backtest backtest backtest backtest backtest recent recent recent recent"
      "forum forum forum forum upgrade upgrade upgrade upgrade progress progress progress progress";
  }
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(12, 1fr);
    grid-template-areas:
      "backtest backtest backtest backtest backtest backtest backtest backtest backtest backtest backtest backtest"
      "recent recent recent recent recent recent recent recent recent recent recent recent"
      "forum forum forum forum forum forum upgrade upgrade upgrade upgrade upgrade upgrade"
      "progress progress progress progress progress progress progress progress progress progress progress progress";
  }

  .page-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "backtest"
      "recent"
      "forum"
      "upgrade"
      "progress";
  }
}
</style>
