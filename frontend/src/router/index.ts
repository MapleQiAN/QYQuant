import { createRouter, createWebHistory } from 'vue-router'
import { toast } from '../lib/toast'
import { pinia } from '../stores/pinia'
import { useUserStore } from '../stores/user'
import DashboardView from '../views/DashboardView.vue'
import BacktestsView from '../views/BacktestsView.vue'
import BacktestResultView from '../views/BacktestResultView.vue'
import BotsView from '../views/BotsView.vue'
import ForumView from '../views/ForumView.vue'
import PostDetailView from '../views/PostDetailView.vue'
import SettingsView from '../views/SettingsView.vue'
import NewStrategyView from '../views/NewStrategyView.vue'
import StrategyLibraryView from '../views/StrategyLibraryView.vue'
import StrategyDetailView from '../views/StrategyDetailView.vue'
import MarketplaceView from '../views/Marketplace.vue'
import MarketplaceStrategyDetailView from '../views/MarketplaceStrategyDetailView.vue'
import PricingView from '../views/PricingView.vue'
import UserProfileView from '../views/UserProfileView.vue'
import AdminDashboardView from '../views/admin/AdminDashboard.vue'
import StrategyReviewView from '../views/admin/StrategyReview.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/strategies', name: 'strategy-library', component: StrategyLibraryView },
    { path: '/strategies/new', name: 'strategy-new', component: NewStrategyView },
    { path: '/strategies/:strategyId/parameters', name: 'strategy-parameters', component: StrategyDetailView },
    { path: '/backtest/configure', name: 'backtest-configure', component: StrategyDetailView },
    { path: '/marketplace', name: 'marketplace', component: MarketplaceView },
    { path: '/marketplace/strategies/:strategyId', name: 'marketplace-strategy-detail', component: MarketplaceStrategyDetailView },
    { path: '/backtests', name: 'backtests', component: BacktestsView },
    { path: '/pricing', name: 'pricing', component: PricingView },
    { path: '/admin', name: 'admin-dashboard', component: AdminDashboardView, meta: { requiresAdmin: true } },
    { path: '/admin/strategies', name: 'admin-strategy-review', component: StrategyReviewView, meta: { requiresAdmin: true } },
    { path: '/backtests/:jobId/report', name: 'backtest-report', component: BacktestResultView },
    { path: '/bots', name: 'bots', component: BotsView },
    { path: '/forum', name: 'forum', component: ForumView },
    { path: '/forum/posts/:postId', name: 'forum-post-detail', component: PostDetailView },
    { path: '/users/:id', name: 'user-profile', component: UserProfileView },
    { path: '/settings', name: 'settings', component: SettingsView }
  ]
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAdmin) {
    return true
  }

  const userStore = useUserStore(pinia)
  if (userStore.token && !userStore.profileLoaded && !userStore.profileLoading) {
    await userStore.loadProfile()
  }

  if (userStore.profile.role === 'admin') {
    return true
  }

  toast.error('无权限')
  return { path: '/' }
})

export default router
