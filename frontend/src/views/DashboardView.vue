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

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">{{ $t('dashboard.totalReturn') }}</div>
        <div class="kpi-value-row">
          <span class="kpi-value tnum" :class="kpiReturn >= 0 ? 'positive' : 'negative'">
            {{ kpiReturn >= 0 ? '+' : '' }}{{ kpiReturn.toFixed(2) }}%
          </span>
          <span class="kpi-badge" :class="kpiReturn >= 0 ? 'badge-success' : 'badge-danger'">
            {{ kpiReturn >= 0 ? $t('dashboard.profit') : $t('dashboard.loss') }}
          </span>
        </div>
        <div class="kpi-sub">{{ $t('dashboard.allStrategiesCombined') }}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{{ $t('dashboard.activeBots') }}</div>
        <div class="kpi-value-row">
          <span class="kpi-value tnum">{{ activeBotCount }}</span>
          <span v-if="activeBotCount > 0" class="kpi-dot active" />
        </div>
        <div class="kpi-sub">{{ $t('dashboard.runningInRealtime') }}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{{ $t('dashboard.strategies') }}</div>
        <div class="kpi-value-row">
          <span class="kpi-value tnum">{{ strategyCount }}</span>
        </div>
        <div class="kpi-sub">{{ $t('dashboard.inYourLibrary') }}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{{ $t('dashboard.backtests') }}</div>
        <div class="kpi-value-row">
          <span class="kpi-value tnum">{{ backtestCount }}</span>
        </div>
        <div class="kpi-sub">{{ $t('dashboard.completedRuns') }}</div>
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
</script>

<style scoped>
.dashboard-view {
  width: 100%;
  max-width: min(1280px, calc(100% - var(--spacing-lg) * 2));
}

/* ── Page Header — Bauhaus ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  position: relative;
  padding-bottom: var(--spacing-lg);
}

.page-header::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  height: 6px;
  background: var(--color-accent);
  border-radius: 3px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: var(--font-size-xxxl);
  font-weight: 900;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.02em;
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

/* ── KPI Row — Bauhaus Cards ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.kpi-card {
  padding: 20px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.kpi-card::after {
  content: "";
  position: absolute;
  height: 4px;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-primary);
  border-radius: 0 0 14px 14px;
}

.kpi-card:nth-child(1)::after { background: var(--color-up); }
.kpi-card:nth-child(2)::after { background: #269A8F; }
.kpi-card:nth-child(3)::after { background: var(--color-accent); }
.kpi-card:nth-child(4)::after { background: var(--color-danger); }

.kpi-card:nth-child(2)::before {
  content: "";
  position: absolute;
  width: 36px;
  height: 36px;
  background: #269A8F;
  border-radius: 50%;
  top: -10px;
  right: -10px;
  opacity: 0.85;
}

.kpi-card:nth-child(3)::before {
  content: "";
  position: absolute;
  width: 30px;
  height: 30px;
  background: var(--color-accent);
  bottom: 12px;
  right: -8px;
  transform: rotate(20deg);
  border-radius: 8px;
  opacity: 0.85;
}

.kpi-label {
  font-size: 11px;
  font-weight: 800;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.kpi-value-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.kpi-value {
  font-size: var(--font-size-xxxl);
  font-weight: 900;
  color: var(--color-text-primary);
  line-height: 1.1;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.kpi-value.positive { color: var(--color-positive); }
.kpi-value.negative { color: var(--color-negative); }

.kpi-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-weight: 800;
  border: 2px solid transparent;
}

.kpi-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-text-muted);
  border: 2px solid var(--color-border);
}

.kpi-dot.active {
  background: var(--color-success);
}

.kpi-sub {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 600;
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

.grid-area-backtest { grid-area: backtest; }
.grid-area-recent { grid-area: recent; }
.grid-area-forum { grid-area: forum; }

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

/* Large screens */
@media (min-width: 1920px) {
  .dashboard-view { max-width: min(1760px, 100%); }
  .dashboard-grid {
    grid-template-columns: 1fr 1fr 380px;
    gap: var(--grid-gap);
  }
}

@media (min-width: 2560px) {
  .dashboard-view { max-width: min(2400px, 100%); }
  .dashboard-grid { grid-template-columns: 1fr 1fr 460px; }
}

/* Responsive */
@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "backtest backtest"
      "recent   forum"
      "sidebar  sidebar";
  }
  .grid-area-sidebar { flex-direction: row; }
  .grid-area-sidebar > * { flex: 1; }
}

@media (max-width: 1024px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
  .header-actions { width: 100%; }
  .header-actions .btn { flex: 1; }
  .kpi-row { grid-template-columns: repeat(2, 1fr); gap: var(--spacing-sm); }
  .kpi-card { padding: 14px; }
  .kpi-card:nth-child(2)::before,
  .kpi-card:nth-child(3)::before { display: none; }
  .kpi-value { font-size: var(--font-size-xxl); }
  .dashboard-grid {
    grid-template-columns: 1fr;
    grid-template-areas: "backtest" "recent" "forum" "sidebar";
  }
  .grid-area-sidebar { flex-direction: column; }
}

@media (max-width: 480px) {
  .dashboard-view { max-width: 100%; }
  .kpi-row { gap: 8px; }
  .kpi-card { padding: 12px; }
  .kpi-value { font-size: var(--font-size-xl); }
}
</style>
