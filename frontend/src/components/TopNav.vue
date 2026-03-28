<template>
  <nav class="top-nav">
    <div class="nav-content">
      <div class="nav-logo">
        <div class="logo-icon">
          <img :src="logoUrl" alt="QY Quant Logo" class="logo-image" />
        </div>
        <span class="logo-text">QY Quant</span>
      </div>

      <div class="nav-links">
        <RouterLink
          v-for="item in navItems"
          :key="item.id"
          :to="item.to"
          :class="['nav-link', { active: route.path === item.to, 'onboarding-highlight': onboardingHighlightTarget === item.target }]"
          :data-onboarding-target="item.target"
        >
          <component :is="getIcon(item.icon)" class="nav-icon" />
          <span>{{ $t(item.label) }}</span>
        </RouterLink>
      </div>

      <div class="nav-right">
        <div class="search-box">
          <SearchIcon class="search-icon" />
          <input type="text" :placeholder="$t('common.searchPlaceholder')" class="search-input" />
        </div>

        <div class="nav-actions">
          <button class="nav-btn" type="button" :aria-label="userStore.theme === 'dark' ? '切换为浅色模式' : '切换为深色模式'" @click="userStore.toggleTheme()">
            <MoonIcon v-if="userStore.theme === 'light'" />
            <SunIcon v-else />
          </button>

          <button class="nav-btn" type="button" aria-label="帮助中心" @click="userStore.setHelpPanelOpen(true)">
            <HelpIcon />
          </button>

          <div class="notification-shell">
            <button class="nav-btn" type="button" aria-label="通知中心" @click="toggleNotifications">
              <BellIcon />
              <span v-if="notificationCount > 0" class="notification-badge">
                {{ notificationCount }}
              </span>
            </button>
            <NotificationPanel v-if="isNotificationPanelOpen" />
          </div>

          <div class="user-menu-shell">
            <button class="user-avatar" type="button" @click="handleAvatarClick">
              <span class="avatar-text">{{ profile.avatar }}</span>
              <span class="user-level">{{ profile.level }}</span>
            </button>
            <div v-if="isUserMenuOpen" class="user-dropdown">
              <RouterLink class="dropdown-item" :to="`/users/${profile.id}`" @click="isUserMenuOpen = false">
                个人主页
              </RouterLink>
              <RouterLink class="dropdown-item" to="/settings" @click="isUserMenuOpen = false">
                设置
              </RouterLink>
              <button class="dropdown-item danger" type="button" @click="handleLogout">
                退出登录
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'
import NotificationPanel from './NotificationPanel.vue'
import { useNotificationStore } from '../stores/useNotificationStore'
import { useUserStore } from '../stores/user'
import logoUrl from '../logo.png'

const route = useRoute()

const navItems = [
  { id: 'dashboard', to: '/', icon: 'chart', label: 'nav.dashboard', target: null },
  { id: 'strategies', to: '/strategies', icon: 'target', label: 'common.newStrategy', target: 'strategy-library-entry' },
  { id: 'backtests', to: '/backtests', icon: 'chart', label: 'nav.backtests', target: null },
  { id: 'bots', to: '/bots', icon: 'robot', label: 'nav.bots', target: null },
  { id: 'forum', to: '/forum', icon: 'users', label: 'nav.forum', target: null },
]

const userStore = useUserStore()
const notificationStore = useNotificationStore()
const { profile, onboardingHighlightTarget } = storeToRefs(userStore)
const notificationCount = computed(() => notificationStore.unreadCount)
const isNotificationPanelOpen = ref(false)
const isUserMenuOpen = ref(false)

function handleAvatarClick() {
  if (!userStore.token) {
    window.location.href = '/login'
    return
  }
  isUserMenuOpen.value = !isUserMenuOpen.value
}

function handleLogout() {
  isUserMenuOpen.value = false
  localStorage.removeItem('qyquant-token')
  window.location.href = '/login'
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-shell')) {
    isUserMenuOpen.value = false
  }
  if (!target.closest('.notification-shell')) {
    isNotificationPanelOpen.value = false
  }
}

onMounted(() => {
  notificationStore.startPolling()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  notificationStore.stopPolling()
  document.removeEventListener('click', handleClickOutside)
})

function toggleNotifications() {
  isNotificationPanelOpen.value = !isNotificationPanelOpen.value
}

const ChartIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 3v18h18' }),
  h('path', { d: 'M18 17V9' }),
  h('path', { d: 'M13 17V5' }),
  h('path', { d: 'M8 17v-3' })
])

const RobotIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('rect', { x: 3, y: 11, width: 18, height: 10, rx: 2 }),
  h('circle', { cx: 12, cy: 5, r: 2 }),
  h('path', { d: 'M12 7v4' }),
  h('line', { x1: 8, y1: 16, x2: 8, y2: 16 }),
  h('line', { x1: 16, y1: 16, x2: 16, y2: 16 })
])

const UsersIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' }),
  h('circle', { cx: 9, cy: 7, r: 4 }),
  h('path', { d: 'M23 21v-2a4 4 0 0 0-3-3.87' }),
  h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' })
])

const HelpIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4' }),
  h('line', { x1: 12, y1: 17, x2: 12.01, y2: 17 }),
])

const SearchIcon = () => h('svg', {
  width: 14,
  height: 14,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 11, cy: 11, r: 8 }),
  h('path', { d: 'm21 21-4.3-4.3' })
])

const BellIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9' }),
  h('path', { d: 'M10.3 21a1.94 1.94 0 0 0 3.4 0' })
])

const TargetIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('circle', { cx: 12, cy: 12, r: 6 }),
  h('circle', { cx: 12, cy: 12, r: 2 }),
])

const SunIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 5 }),
  h('line', { x1: 12, y1: 1, x2: 12, y2: 3 }),
  h('line', { x1: 12, y1: 21, x2: 12, y2: 23 }),
  h('line', { x1: 4.22, y1: 4.22, x2: 5.64, y2: 5.64 }),
  h('line', { x1: 18.36, y1: 18.36, x2: 19.78, y2: 19.78 }),
  h('line', { x1: 1, y1: 12, x2: 3, y2: 12 }),
  h('line', { x1: 21, y1: 12, x2: 23, y2: 12 }),
  h('line', { x1: 4.22, y1: 19.78, x2: 5.64, y2: 18.36 }),
  h('line', { x1: 18.36, y1: 5.64, x2: 19.78, y2: 4.22 }),
])

const MoonIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z' }),
])

const iconMap: Record<string, any> = {
  chart: ChartIcon,
  target: TargetIcon,
  robot: RobotIcon,
  users: UsersIcon
}

function getIcon(iconName: string) {
  return iconMap[iconName] || ChartIcon
}
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-height);
  background: var(--color-nav-bg);
  border-bottom: 1px solid var(--color-nav-border);
}

.nav-content {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  height: 100%;
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.logo-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-text {
  font-size: 15px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 100%;
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 100%;
  padding: 0 12px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.nav-link:hover {
  color: var(--color-text-primary);
}

.nav-link.active {
  color: var(--color-primary-light);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 2px;
  background: var(--color-primary);
  border-radius: 1px 1px 0 0;
}

.nav-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.nav-link:hover .nav-icon,
.nav-link.active .nav-icon {
  opacity: 1;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 200px;
  height: 32px;
  padding: 0 12px 0 32px;
  font-size: var(--font-size-xs);
  font-family: var(--font-family);
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-bg);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-btn {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}

.nav-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.notification-shell {
  position: relative;
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  font-size: 9px;
  font-weight: var(--font-weight-bold);
  background: var(--color-danger);
  color: #fff;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.user-menu-shell {
  position: relative;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 2px 8px 2px 2px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.user-avatar:hover {
  border-color: var(--color-border-hover);
}

.avatar-text {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-sm);
}

.user-level {
  font-size: 10px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-accent);
  letter-spacing: 0.03em;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 150px;
  padding: 4px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 200;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-decoration: none;
  text-align: left;
  transition: background-color var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-item.danger {
  color: var(--color-danger);
}

.dropdown-item.danger:hover {
  background: var(--color-danger-bg);
}

@media (max-width: 1024px) {
  .nav-content {
    gap: 16px;
  }

  .nav-link {
    padding: 0 8px;
  }

  .search-input {
    width: 160px;
  }
}

@media (max-width: 768px) {
  .top-nav {
    height: auto;
  }

  .nav-content {
    flex-wrap: wrap;
    padding: 8px var(--spacing-md);
    gap: 8px;
  }

  .nav-links {
    order: 3;
    width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
    height: auto;
    padding-bottom: 4px;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  .nav-link.active::after {
    bottom: 0;
  }

  .search-input {
    width: 140px;
  }
}
</style>
