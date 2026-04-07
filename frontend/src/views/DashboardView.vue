<template>
  <div class="dashboard-view">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-text">
        <h1 class="page-title">{{ $t('dashboard.title', { name: user.name }) }}</h1>
        <p class="page-subtitle">{{ $t('dashboard.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <RouterLink class="btn btn-secondary" to="/strategies">
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

    <!-- KPI Row - Enterprise Style -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-label-wrapper">
            <TrendingIcon class="kpi-icon" />
            <span class="kpi-label">{{ $t('dashboard.totalReturn') }}</span>
          </div>
          <span class="kpi-badge" :class="kpiReturn >= 0 ? 'badge-success' : 'badge-danger'">
            {{ kpiReturn >= 0 ? $t('dashboard.profit') : $t('dashboard.loss') }}
          </span>
        </div>
        <div class="kpi-value tnum" :class="kpiReturn >= 0 ? 'positive' : 'negative'">
          {{ kpiReturn >= 0 ? '+' : '' }}{{ kpiReturn.toFixed(2) }}%
        </div>
        <div class="kpi-footer">
          <span class="kpi-sub">{{ $t('dashboard.allStrategiesCombined') }}</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-label-wrapper">
            <BotIcon class="kpi-icon" />
            <span class="kpi-label">{{ $t('dashboard.activeBots') }}</span>
          </div>
          <span class="kpi-indicator active" />
        </div>
        <div class="kpi-value tnum">{{ activeBotCount }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">{{ $t('dashboard.runningInRealtime') }}</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-label-wrapper">
            <StrategyIcon class="kpi-icon" />
            <span class="kpi-label">{{ $t('dashboard.strategies') }}</span>
          </div>
        </div>
        <div class="kpi-value tnum">{{ strategyCount }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">{{ $t('dashboard.inYourLibrary') }}</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-label-wrapper">
            <BacktestIcon class="kpi-icon" />
            <span class="kpi-label">{{ $t('dashboard.backtests') }}</span>
          </div>
        </div>
        <div class="kpi-value tnum">{{ backtestCount }}</div>
        <div class="kpi-footer">
          <span class="kpi-sub">{{ $t('dashboard.completedRuns') }}</span>
        </div>
      </div>
    </div>

    <!-- Main Grid -->
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

      <div class="grid-area-sidebar">
        <UpgradeCard v-if="isFreePlan" @upgrade="handleOpenPricing" />
        <ProgressCard />
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
import { PLAN_TIER_ORDER } from '../data/plans'
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

const isFreePlan = computed(() => {
  const tier = PLAN_TIER_ORDER[user.value.plan_level] ?? 0
  return tier === 0
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

const PlusIcon = () => h('svg', {
  width: 14,
  height: 14,
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

// KPI Icons
const TrendingIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('polyline', { points: '23 6 13.5 15.5 8.5 10.5 1 18' }),
  h('polyline', { points: '17 6 23 6 23 12' })
])

const BotIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('rect', { x: '3', y: '11', width: '18', height: '10', rx: '2' }),
  h('circle', { cx: '12', cy: '5', r: '2' }),
  h('path', { d: 'M12 7v4' }),
  h('line', { x1: '8', y1: '16', x2: '8', y2: '16' }),
  h('line', { x1: '16', y1: '16', x2: '16', y2: '16' })
])

const StrategyIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
  h('polyline', { points: '14 2 14 8 20 8' }),
  h('line', { x1: '16', y1: '13', x2: '8', y2: '13' }),
  h('line', { x1: '16', y1: '17', x2: '8', y2: '17' }),
  h('polyline', { points: '10 9 9 9 8 9' })
])

const BacktestIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: '12', cy: '12', r: '10' }),
  h('polyline', { points: '12 6 12 12 16 14' })
])
</script>

<style scoped>
.dashboard-view {
  width: 100%;
  max-width: min(1280px, calc(100% - var(--spacing-lg) * 2));
}

@media (min-width: 1920px) {
  .dashboard-view {
    max-width: min(1760px, 100%);
  }

  .kpi-row {
    grid-template-columns: repeat(4, 1fr);
    gap: var(--grid-gap);
  }

  .kpi-card {
    padding: 20px 24px;
  }

  .kpi-value {
    font-size: var(--font-size-display);
  }

  .dashboard-grid {
    grid-template-columns: 1fr 1fr 380px;
    gap: var(--grid-gap);
  }
}

@media (min-width: 2560px) {
  .dashboard-view {
    max-width: min(2400px, 100%);
  }

  .kpi-row {
    gap: var(--grid-gap);
  }

  .kpi-card {
    padding: 24px 28px;
  }

  .kpi-value {
    font-size: var(--font-size-display);
  }

  .dashboard-grid {
    grid-template-columns: 1fr 1fr 460px;
    gap: var(--grid-gap);
  }
}

@media (min-width: 3840px) {
  .dashboard-view {
    max-width: min(3600px, 100%);
  }

  .kpi-card {
    padding: 32px 36px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr 1fr 600px;
    gap: var(--grid-gap);
  }
}

/* ── Page Header ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: var(--letter-spacing-tight);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* ── KPI Row - Enterprise Financial ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.kpi-card {
  position: relative;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-normal);
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-border-hover);
  transition: background var(--transition-normal);
}

.kpi-card:hover {
  border-color: var(--color-border-hover);
}

.kpi-card:first-child::before {
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
}

.kpi-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.kpi-label-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.kpi-icon {
  color: var(--color-text-muted);
  opacity: 0.7;
  flex-shrink: 0;
}

.kpi-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  letter-spacing: 0.02em;
}

.kpi-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.kpi-indicator {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-text-muted);
}

.kpi-indicator.active {
  background: var(--color-success);
  box-shadow: 0 0 0 3px var(--color-success-bg);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 0 3px var(--color-success-bg); }
  50% { box-shadow: 0 0 0 6px transparent; }
}

.kpi-value {
  font-size: var(--font-size-xxxl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.1;
  letter-spacing: var(--letter-spacing-tight);
  margin-bottom: 6px;
}

.kpi-value.positive {
  color: var(--color-positive);
}

.kpi-value.negative {
  color: var(--color-negative);
}

.kpi-footer {
  display: flex;
  align-items: center;
}

.kpi-sub {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-normal);
}

/* ── Dashboard Grid ── */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 320px;
  grid-template-rows: auto auto;
  gap: var(--spacing-md);
  grid-template-areas:
    "backtest backtest sidebar"
    "recent   forum    sidebar";
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

.grid-area-sidebar {
  grid-area: sidebar;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.grid-area-backtest > *,
.grid-area-recent > *,
.grid-area-forum > * {
  height: 100%;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "backtest backtest"
      "recent   forum"
      "sidebar  sidebar";
  }

  .grid-area-sidebar {
    flex-direction: row;
  }

  .grid-area-sidebar > * {
    flex: 1;
  }
}

@media (max-width: 1024px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .kpi-value {
    font-size: var(--font-size-xxl);
  }

  .kpi-icon {
    width: 15px;
    height: 15px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }

  .page-title {
    font-size: var(--font-size-xl);
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn {
    flex: 1;
  }

  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-sm);
  }

  .kpi-card {
    padding: 12px 14px;
  }

  .kpi-value {
    font-size: var(--font-size-xxl);
  }

  .kpi-icon {
    width: 15px;
    height: 15px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "backtest"
      "recent"
      "forum"
      "sidebar";
  }

  .grid-area-sidebar {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .dashboard-view {
    max-width: 100%;
  }

  .page-header {
    margin-bottom: var(--spacing-sm);
  }

  .kpi-row {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: var(--spacing-sm);
  }

  .kpi-card {
    padding: 10px 12px;
  }

  .kpi-value {
    font-size: var(--font-size-xl);
  }

  .kpi-icon {
    width: 14px;
    height: 14px;
  }

  .kpi-label {
    font-size: 11px;
  }

  .kpi-badge {
    font-size: 10px;
    padding: 2px 6px;
  }

  .kpi-sub {
    font-size: 11px;
  }
}
</style>
