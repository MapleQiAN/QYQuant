import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import BacktestsView from '../views/BacktestsView.vue'
import BotsView from '../views/BotsView.vue'
import ForumView from '../views/ForumView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/backtests', name: 'backtests', component: BacktestsView },
    { path: '/bots', name: 'bots', component: BotsView },
    { path: '/forum', name: 'forum', component: ForumView },
    { path: '/settings', name: 'settings', component: SettingsView }
  ]
})

export default router
