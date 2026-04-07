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
import StrategyImportView from '../views/StrategyImportView.vue'
import StrategyImportConfirmView from '../views/StrategyImportConfirmView.vue'
import StrategyDetailView from '../views/StrategyDetailView.vue'
import MarketplaceView from '../views/Marketplace.vue'
import MarketplaceStrategyDetailView from '../views/MarketplaceStrategyDetailView.vue'
import PricingView from '../views/PricingView.vue'
import CheckoutView from '../views/CheckoutView.vue'
import LearnView from '../views/LearnView.vue'
import UserProfileView from '../views/UserProfileView.vue'
import AdminDashboardView from '../views/admin/AdminDashboard.vue'
import BacktestMonitorView from '../views/admin/BacktestMonitor.vue'
import LoginView from '../views/LoginView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import DataSourceHealthView from '../views/admin/DataSourceHealth.vue'
import ReportManagementView from '../views/admin/ReportManagement.vue'
import StrategyReviewView from '../views/admin/StrategyReview.vue'
import UserManagementView from '../views/admin/UserManagement.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to) {
    if (to.hash) {
      return {
        el: to.hash,
        top: 88,
        behavior: 'smooth',
      }
    }

    return { top: 0 }
  },
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { hideChrome: true } },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView, meta: { hideChrome: true } },
    { path: '/reset-password', name: 'reset-password', component: ResetPasswordView, meta: { hideChrome: true } },
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/learn', name: 'learn', component: LearnView },
    { path: '/strategies', name: 'strategy-library', component: StrategyLibraryView },
    { path: '/strategies/new', name: 'strategy-new', component: NewStrategyView },
    { path: '/strategies/import', name: 'strategy-import', component: StrategyImportView },
    { path: '/strategies/import/confirm', name: 'strategy-import-confirm', component: StrategyImportConfirmView },
    { path: '/strategies/:strategyId/parameters', name: 'strategy-parameters', component: StrategyDetailView },
    { path: '/backtest/configure', name: 'backtest-configure', component: StrategyDetailView },
    { path: '/marketplace', name: 'marketplace', component: MarketplaceView },
    { path: '/marketplace/strategies/:strategyId', name: 'marketplace-strategy-detail', component: MarketplaceStrategyDetailView },
    { path: '/backtests', name: 'backtests', component: BacktestsView },
    { path: '/pricing', name: 'pricing', component: PricingView },
    { path: '/checkout', name: 'checkout', component: CheckoutView },
    { path: '/admin', name: 'admin-dashboard', component: AdminDashboardView, meta: { requiresAdmin: true } },
    { path: '/admin/backtest-monitor', name: 'admin-backtest-monitor', component: BacktestMonitorView, meta: { requiresAdmin: true } },
    { path: '/admin/data-source-health', name: 'admin-data-source-health', component: DataSourceHealthView, meta: { requiresAdmin: true } },
    { path: '/admin/strategies', name: 'admin-strategy-review', component: StrategyReviewView, meta: { requiresAdmin: true } },
    { path: '/admin/reports', name: 'admin-report-management', component: ReportManagementView, meta: { requiresAdmin: true } },
    { path: '/admin/user-management', name: 'admin-user-management', component: UserManagementView, meta: { requiresAdmin: true } },
    { path: '/backtests/:jobId/report', name: 'backtest-report', component: BacktestResultView },
    { path: '/bots', name: 'bots', component: BotsView },
    { path: '/forum', name: 'forum', component: ForumView },
    { path: '/forum/posts/:postId', name: 'forum-post-detail', component: PostDetailView },
    { path: '/users/:id', name: 'user-profile', component: UserProfileView },
    { path: '/settings', name: 'settings', component: SettingsView }
  ]
})

const publicRoutes = new Set(['login', 'forgot-password', 'reset-password'])

router.beforeEach(async (to) => {
  const userStore = useUserStore(pinia)
  const isPublic = publicRoutes.has(to.name as string)

  // Load profile if token exists but profile not yet loaded
  if (userStore.token && !userStore.profileLoaded && !userStore.profileLoading) {
    await userStore.loadProfile()
  }

  // Redirect logged-in users away from auth pages
  if (isPublic && userStore.token) {
    return { path: '/' }
  }

  // Redirect unauthenticated users to login (except public pages)
  if (!isPublic && !userStore.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // Admin-only check
  if (to.meta.requiresAdmin && userStore.profile.role !== 'admin') {
    toast.error('无权限')
    return { path: '/' }
  }

  return true
})

export default router
