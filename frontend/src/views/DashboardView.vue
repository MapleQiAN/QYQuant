<template>
  <div class="dashboard-view">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-text">
          <h1 class="page-title">Welcome back, {{ user.name }}</h1>
          <p class="page-subtitle">Here is your trading dashboard overview.</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary">
            <SettingsIcon />
            Settings
          </button>
          <button class="btn btn-primary">
            <PlusIcon />
            New Strategy
          </button>
        </div>
      </div>

      <!-- Dashboard Grid -->
      <div class="dashboard-grid">
        <!-- Left: Backtest Overview Card (8 cols) -->
        <div class="grid-area-backtest">
          <BacktestCard />
        </div>

        <!-- Right: Recent List (4 cols) -->
        <div class="grid-area-recent">
          <RecentList title="Recent activity" />
        </div>

        <!-- Bottom Row: Three Cards -->
        <div class="grid-area-forum">
          <ForumMiniCard />
        </div>

        <div class="grid-area-upgrade">
          <UpgradeCard />
        </div>

        <div class="grid-area-progress">
          <ProgressCard />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'
import BacktestCard from '../components/BacktestCard.vue'
import ForumMiniCard from '../components/ForumMiniCard.vue'
import ProgressCard from '../components/ProgressCard.vue'
import RecentList from '../components/RecentList.vue'
import UpgradeCard from '../components/UpgradeCard.vue'
import { mockUser } from '../data/mockData'

const user = mockUser

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
