<template>
  <div class="dashboard-terminal">
    <OnboardingGuide
      :visible="showOnboardingGuide"
      @skip="handleSkipOnboarding"
      @focus-target="userStore.setOnboardingHighlightTarget"
      @launch-guided-backtest="userStore.startGuidedBacktest()"
      @complete="handleSkipOnboarding"
    />

    <!-- KPI Ticker Strip -->
    <div class="ticker-strip">
      <div class="ticker-item">
        <span class="ticker-label">P&L</span>
        <span class="ticker-value tnum" :class="kpiReturn >= 0 ? 'positive' : 'negative'">
          {{ kpiReturn >= 0 ? '+' : '' }}{{ kpiReturn.toFixed(2) }}%
        </span>
      </div>
      <div class="ticker-sep">|</div>
      <div class="ticker-item">
        <span class="ticker-label">BOTS</span>
        <span class="ticker-value tnum">{{ activeBotCount }}</span>
      </div>
      <div class="ticker-sep">|</div>
      <div class="ticker-item">
        <span class="ticker-label">STRAT</span>
        <span class="ticker-value tnum">{{ strategyCount }}</span>
      </div>
      <div class="ticker-sep">|</div>
      <div class="ticker-item">
        <span class="ticker-label">TESTS</span>
        <span class="ticker-value tnum">{{ backtestCount }}</span>
      </div>
      <div class="ticker-sep">|</div>
      <div class="ticker-item">
        <span class="ticker-label">SYM</span>
        <span class="ticker-value tnum">{{ backtestQuery.symbol }}</span>
      </div>
      <div class="ticker-spacer" />
      <div class="ticker-actions">
        <RouterLink class="ticker-btn" to="/strategies">
          <PlusIcon /> {{ $t('common.newStrategy') }}
        </RouterLink>
      </div>
    </div>

    <!-- Workspace Grid -->
    <div class="workspace">
      <!-- Main Panel: Backtest -->
      <div class="workspace-main">
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

      <!-- Right Sidebar: Stacked Panels -->
      <div class="workspace-sidebar">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import BacktestCard from '../components/BacktestCard.vue'
import ForumMiniCard from '../components/ForumMiniCard.vue'
import OnboardingGuide from '../components/onboarding/OnboardingGuide.vue'
import RecentList from '../components/RecentList.vue'
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

// KPI computed values
const kpiReturn = computed(() => {
  const latest = backtestsStore.latest
  return latest?.summary?.totalReturn ?? 0
})
const activeBotCount = computed(() => {
  return botsStore.recent?.filter((b: any) => b.status === 'running').length ?? 0
})
const strategyCount = computed(() => strategiesStore.recent?.length ?? 0)
const backtestCount = computed(() => backtestsStore.latest ? 1 : 0)

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

const PlusIcon = () => h('svg', {
  width: 12, height: 12, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M5 12h14' }),
  h('path', { d: 'M12 5v14' })
])
</script>

<style scoped>
.dashboard-terminal {
  display: flex;
  flex-direction: column;
  gap: var(--grid-gap);
  height: calc(100vh - var(--status-bar-height) - var(--spacing-md) * 2);
}

/* ── Ticker Strip ── */
.ticker-strip {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 0 var(--spacing-md);
  height: 36px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  flex-shrink: 0;
  overflow: hidden;
}

.ticker-item {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.ticker-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-2xs);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.05em;
}

.ticker-value {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.ticker-value.positive {
  color: var(--color-positive);
}

.ticker-value.negative {
  color: var(--color-negative);
}

.ticker-sep {
  color: var(--color-border);
  font-size: var(--font-size-sm);
  user-select: none;
}

.ticker-spacer {
  flex: 1;
}

.ticker-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.ticker-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: var(--font-size-2xs);
  font-family: var(--font-family);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  background: var(--color-primary-bg);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.ticker-btn:hover {
  background: var(--color-primary);
  color: #fff;
}

/* ── Workspace Grid ── */
.workspace {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--grid-gap);
  flex: 1;
  min-height: 0;
}

.workspace-main {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.workspace-main > * {
  flex: 1;
  min-height: 0;
}

.workspace-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--grid-gap);
  min-height: 0;
  overflow: hidden;
}

.workspace-sidebar > * {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .workspace {
    grid-template-columns: 1fr 320px;
  }
}

@media (max-width: 1024px) {
  .dashboard-terminal {
    height: auto;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .workspace-sidebar {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .ticker-strip {
    gap: var(--spacing-sm);
    padding: 0 var(--spacing-sm);
    font-size: var(--font-size-2xs);
  }

  .ticker-actions {
    display: none;
  }
}
</style>
