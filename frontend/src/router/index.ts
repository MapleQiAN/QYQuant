import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import BacktestsView from '../views/BacktestsView.vue'
import BacktestResultView from '../views/BacktestResultView.vue'
import BotsView from '../views/BotsView.vue'
import ForumView from '../views/ForumView.vue'
import SettingsView from '../views/SettingsView.vue'
import NewStrategyView from '../views/NewStrategyView.vue'
import StrategyLibraryView from '../views/StrategyLibraryView.vue'
import StrategyDetailView from '../views/StrategyDetailView.vue'
import MarketplaceView from '../views/Marketplace.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/strategies', name: 'strategy-library', component: StrategyLibraryView },
    { path: '/strategies/new', name: 'strategy-new', component: NewStrategyView },
    { path: '/strategies/:strategyId/parameters', name: 'strategy-detail', component: StrategyDetailView },
    { path: '/marketplace', name: 'marketplace', component: MarketplaceView },
    { path: '/backtests', name: 'backtests', component: BacktestsView },
    { path: '/backtests/:jobId/report', name: 'backtest-report', component: BacktestResultView },
    { path: '/bots', name: 'bots', component: BotsView },
    { path: '/forum', name: 'forum', component: ForumView },
    { path: '/settings', name: 'settings', component: SettingsView }
  ]
})

export default router
